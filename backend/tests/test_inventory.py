import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ['STOCKCORE_API_KEY'] = 'test-only-key'
os.environ['FRONTEND_URL'] = 'https://stock.example.com'
from database import get_session
from main import app
from models import StockBalance, StockMovement

@pytest.fixture
def inventory(tmp_path, monkeypatch):
    url = os.getenv('TEST_DATABASE_URL') or 'sqlite://'
    monkeypatch.setenv('DATABASE_URL', url)
    if url == 'sqlite://':
        engine = create_engine(url, connect_args={'check_same_thread': False}, poolclass=StaticPool)
        @event.listens_for(engine, 'connect')
        def foreign_keys(connection, unused):
            connection.execute('PRAGMA foreign_keys=ON')
        # Use the same connection for the migration on the in-memory test database.
        config = Config('alembic.ini')
        with engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
    else:
        # TEST_DATABASE_URL must point to a disposable, dedicated test database.
        engine = create_engine(url)
        config = Config('alembic.ini')
        command.upgrade(config, 'head')
    factory = sessionmaker(engine, expire_on_commit=False)
    def session():
        with factory() as db:
            yield db
    app.dependency_overrides[get_session] = session
    with TestClient(app) as client:
        client.headers['X-API-Key'] = 'test-only-key'
        yield client, factory, engine
    app.dependency_overrides.clear()
    if url != 'sqlite://':
        command.downgrade(config, 'base')
    engine.dispose()

def setup(client):
    category = client.post('/api/categories', json={'name': 'Insumos'}).json()['id']
    p = client.post('/api/products', json={'name': 'Tornillo', 'sku': 'tor-01', 'category_id': category, 'price': '12.50'})
    assert p.status_code == 201
    w = client.post('/api/warehouses', json={'name': 'Principal', 'address': 'San Juan'})
    assert w.status_code == 201
    client.post('/api/responsibles', json={'name': 'Operador', 'employee_code': 'TEST-1', 'sector': 'Pruebas'})
    return p.json()['id'], w.json()['id']

def payload(p, w, kind='entry', quantity='10.125'):
    return {'request_id': str(uuid4()), 'product_id': p, 'warehouse_id': w,
            'kind': kind, 'quantity': quantity, 'reason_id': 8, 'responsible_id': 1}

def test_persistence_idempotency_and_insufficient_stock(inventory):
    client, factory, engine = inventory
    p, w = setup(client)
    data = payload(p, w)
    first = client.post('/api/movements', json=data)
    assert first.status_code == 200
    assert client.post('/api/movements', json=data).json()['id'] == first.json()['id']
    assert client.post('/api/movements', json={**data, 'quantity': '11'}).status_code == 409
    assert client.post('/api/movements', json=payload(p, w, 'exit', '11')).status_code == 409
    assert client.post('/api/movements', json=payload(p, w, 'exit', '0.125')).status_code == 200
    with factory() as db:
        assert db.get(StockBalance, (p, w)).quantity == Decimal('10.000')
        assert db.scalar(select(func.count()).select_from(StockMovement)) == 2
    assert Decimal(str(client.get('/api/stock').json()['stock'][0]['quantity'])) == 10
    assert Decimal(str(client.get('/api/products').json()['products'][0]['quantity'])) == 10
    assert client.get('/api/ready').json()['ready'] is True

def test_validation_auth_and_warehouses(inventory):
    client, factory, engine = inventory
    p, w = setup(client)
    assert client.get('/api/products', headers={'X-API-Key': 'wrong'}).status_code == 401
    assert client.post('/api/products', json={'name': 'Otro', 'sku': 'TOR-01'}).status_code == 409
    assert client.post('/api/products', json={'name': 'Otro', 'sku': 'NEW', 'category_id': 999}).status_code == 404
    for amount in ['0', '-1', '0.0001', 'NaN']:
        assert client.post('/api/movements', json=payload(p, w, quantity=amount)).status_code == 422
    assert client.post('/api/movements', json=payload(p, 999)).status_code == 404
    second = client.post('/api/warehouses', json={'name': 'Secundario'}).json()['id']
    assert client.post('/api/movements', json=payload(p, w)).status_code == 200
    assert client.post('/api/movements', json=payload(p, second, 'exit', '1')).status_code == 409
    assert client.post('/api/movements', json=payload(p, second, 'entry', '2')).status_code == 200
    assert len(client.get('/api/stock').json()['stock']) == 2
    assert len(client.get(f'/api/stock?warehouse_id={second}').json()['stock']) == 1
    response = client.options('/api/movements', headers={'Origin': 'https://stock.example.com',
        'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'X-API-Key,Content-Type'})
    assert response.headers['access-control-allow-origin'] == 'https://stock.example.com'

def test_concurrent_exits_cannot_oversell(inventory):
    client, factory, engine = inventory
    if engine.dialect.name != 'postgresql':
        pytest.skip('Requires PostgreSQL row-lock semantics')
    p, w = setup(client)
    assert client.post('/api/movements', json=payload(p, w, quantity='10')).status_code == 200
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(client.post, '/api/movements', json=payload(p, w, 'exit', '7')) for _ in range(2)]
        assert sorted(f.result().status_code for f in futures) == [200, 409]
    with factory() as db:
        assert db.get(StockBalance, (p, w)).quantity == 3
        assert db.scalar(select(func.count()).select_from(StockMovement)) == 2

def test_concurrent_first_entries_and_retries(inventory):
    client, factory, engine = inventory
    if engine.dialect.name != 'postgresql':
        pytest.skip('Requires PostgreSQL row-lock semantics')
    p, w = setup(client)
    data = payload(p, w, quantity='5')
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(client.post, '/api/movements', json=data) for _ in range(2)]
        results = [f.result() for f in futures]
        assert all(r.status_code == 200 for r in results)
        assert results[0].json()['id'] == results[1].json()['id']
    with factory() as db:
        assert db.get(StockBalance, (p, w)).quantity == 5
        assert db.scalar(select(func.count()).select_from(StockMovement)) == 1

def test_catalog_validation_and_historical_snapshots(inventory):
    client, factory, engine = inventory
    p, w = setup(client)
    data = payload(p, w)
    first = client.post('/api/movements', json=data)
    assert first.status_code == 200
    assert first.json()['reason'] == 'Ajuste de inventario'
    reason = client.get('/api/reasons').json()['reasons']
    reason = next(x for x in reason if x['id'] == 8)
    person = client.get('/api/responsibles').json()['responsibles'][0]
    assert client.put('/api/reasons/8', json={**{k:v for k,v in reason.items() if k != 'id'}, 'name': 'Ajuste nuevo', 'active': False}).status_code == 200
    assert client.put('/api/responsibles/1', json={**{k:v for k,v in person.items() if k != 'id'}, 'name': 'Nombre nuevo', 'active': False}).status_code == 200
    assert client.post('/api/movements', json=data).json()['id'] == first.json()['id']
    assert client.post('/api/movements', json=payload(p, w)).status_code == 422
    old = client.get('/api/movements').json()['movements'][0]
    assert old['reason'] == 'Ajuste de inventario' and old['operator'] == 'Operador'
    assert client.post('/api/movements', json={**payload(p, w), 'reason_id': 999}).status_code == 404
    client.put('/api/responsibles/1', json={k:v for k,v in person.items() if k != 'id'})
    assert client.post('/api/movements', json={**payload(p, w, 'exit'), 'reason_id': 1}).status_code == 422

def test_migration_preserves_legacy_history(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    config = Config('alembic.ini')
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        command.upgrade(config, '0001_inventory')
        connection.exec_driver_sql("INSERT INTO warehouses (id,name,address) VALUES (1,'Principal','')")
        connection.exec_driver_sql("INSERT INTO products (id,sku,name,price) VALUES (1,'LEGACY','Producto',10)")
        connection.exec_driver_sql("INSERT INTO stock_balances (product_id,warehouse_id,quantity) VALUES (1,1,5)")
        connection.exec_driver_sql("INSERT INTO stock_movements (request_id,product_id,warehouse_id,kind,quantity,reason,operator) VALUES ('legacy',1,1,'entry',5,'Motivo anterior','Persona anterior')")
        command.upgrade(config, 'head')
        row = connection.exec_driver_sql('SELECT reason,operator,reason_id,responsible_id FROM stock_movements').one()
        assert tuple(row) == ('Motivo anterior', 'Persona anterior', None, None)
        assert connection.exec_driver_sql('SELECT quantity FROM stock_balances').scalar() == 5
    engine.dispose()
