import hmac
import os
from decimal import Decimal
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from database import get_session
from models import Category, Company, Product, StockBalance, StockMovement, Warehouse, MovementReason, Responsible, RecipientCompany, Recipient
from schemas import MovementInput, Named, ProductInput, WarehouseInput, ReasonInput, ResponsibleInput, RecipientCompanyInput, RecipientInput

app = FastAPI(title='StockCore API', version='0.2.0')
origins = ['http://localhost:3000', 'http://localhost']
origins.extend(x.strip().rstrip('/') for x in os.getenv('FRONTEND_URL', '').split(',') if x.strip())
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'OPTIONS'], allow_headers=['Content-Type', 'X-API-Key'])

def authorize(x_api_key: str | None = Header(default=None)):
    expected = os.getenv('STOCKCORE_API_KEY', '')
    if not expected:
        raise HTTPException(503, 'Configure STOCKCORE_API_KEY para habilitar el sistema.')
    if not x_api_key or not hmac.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(401, 'Clave de acceso incorrecta.')

auth = [Depends(authorize)]

@app.exception_handler(IntegrityError)
async def conflict_handler(request, error):
    return JSONResponse(status_code=409, content={'detail': 'El código o nombre ya existe, o la operación infringe una regla de datos.'})

@app.exception_handler(SQLAlchemyError)
async def database_handler(request, error):
    return JSONResponse(status_code=503, content={'detail': 'La base de datos no está disponible. Verifique la conexión y las migraciones.'})

@app.get('/health')
def health():
    return {'status': 'healthy', 'service': 'stockcore-api'}

@app.get('/api/ready', dependencies=auth)
def ready(db: Session = Depends(get_session)):
    db.execute(text('SELECT 1'))
    return {'ready': db.get(Company, 1) is not None}

@app.get('/')
def root():
    return {'message': 'StockCore API', 'version': '0.2.0'}

def require(db, model, record_id):
    item = db.get(model, record_id)
    if item is None:
        raise HTTPException(404, 'Registro no encontrado.')
    return item

def record(item, fields):
    return {field: getattr(item, field) for field in fields}

@app.get('/api/company', dependencies=auth)
def company(db: Session = Depends(get_session)):
    return record(require(db, Company, 1), ['id', 'name'])

@app.put('/api/company', dependencies=auth)
def update_company(data: Named, db: Session = Depends(get_session)):
    item = require(db, Company, 1)
    item.name = data.name
    db.commit()
    return record(item, ['id', 'name'])

@app.get('/api/categories', dependencies=auth)
def categories(db: Session = Depends(get_session)):
    return {'categories': [record(x, ['id', 'name']) for x in db.scalars(select(Category).order_by(Category.name))]}

@app.post('/api/categories', status_code=201, dependencies=auth)
def create_category(data: Named, db: Session = Depends(get_session)):
    item = Category(**data.model_dump())
    db.add(item)
    db.commit()
    return record(item, ['id', 'name'])

@app.get('/api/warehouses', dependencies=auth)
def warehouses(db: Session = Depends(get_session)):
    return {'warehouses': [record(x, ['id', 'name', 'address']) for x in db.scalars(select(Warehouse).order_by(Warehouse.name))]}

@app.post('/api/warehouses', status_code=201, dependencies=auth)
def create_warehouse(data: WarehouseInput, db: Session = Depends(get_session)):
    item = Warehouse(**data.model_dump())
    db.add(item)
    db.commit()
    return record(item, ['id', 'name', 'address'])

@app.get('/api/products', dependencies=auth)
def products(db: Session = Depends(get_session)):
    statement = select(Product, func.coalesce(func.sum(StockBalance.quantity), 0)).outerjoin(
        StockBalance, Product.id == StockBalance.product_id).group_by(Product.id).order_by(Product.name)
    items = [{**record(p, ['id', 'sku', 'name', 'category_id', 'price']), 'quantity': q} for p, q in db.execute(statement)]
    return {'products': items, 'total': len(items)}

@app.post('/api/products', status_code=201, dependencies=auth)
def create_product(data: ProductInput, db: Session = Depends(get_session)):
    if data.category_id:
        require(db, Category, data.category_id)
    item = Product(**data.model_dump())
    db.add(item)
    db.commit()
    return {**record(item, ['id', 'sku', 'name', 'category_id', 'price']), 'quantity': 0}

@app.put('/api/products/{product_id}', dependencies=auth)
def update_product(product_id: int, data: ProductInput, db: Session = Depends(get_session)):
    item = require(db, Product, product_id)
    if data.category_id:
        require(db, Category, data.category_id)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return record(item, ['id', 'sku', 'name', 'category_id', 'price'])

@app.get('/api/stock', dependencies=auth)
def stock(warehouse_id: int | None = None, db: Session = Depends(get_session)):
    statement = select(StockBalance, Product, Warehouse).select_from(StockBalance).join(
        Product, Product.id == StockBalance.product_id).join(Warehouse, Warehouse.id == StockBalance.warehouse_id)
    if warehouse_id is not None:
        require(db, Warehouse, warehouse_id)
        statement = statement.where(StockBalance.warehouse_id == warehouse_id)
    return {'stock': [{'product_id': p.id, 'sku': p.sku, 'product': p.name, 'warehouse_id': w.id,
        'warehouse': w.name, 'quantity': b.quantity} for b, p, w in db.execute(statement.order_by(Warehouse.name, Product.name))]}

movement_fields = ['id', 'request_id', 'product_id', 'warehouse_id', 'kind', 'quantity', 'reason', 'operator', 'reason_id', 'responsible_id', 'recipient_id', 'recipient_name', 'recipient_company', 'reference', 'created_at']

reason_fields = ['id', 'name', 'kind', 'active']
responsible_fields = ['id', 'name', 'employee_code', 'sector', 'active']

@app.get('/api/reasons', dependencies=auth)
def reasons(db: Session = Depends(get_session)):
    return {'reasons': [record(x, reason_fields) for x in db.scalars(select(MovementReason).order_by(MovementReason.name))]}

@app.post('/api/reasons', status_code=201, dependencies=auth)
def create_reason(data: ReasonInput, db: Session = Depends(get_session)):
    item = MovementReason(**data.model_dump())
    db.add(item)
    db.commit()
    return record(item, reason_fields)

@app.put('/api/reasons/{reason_id}', dependencies=auth)
def update_reason(reason_id: int, data: ReasonInput, db: Session = Depends(get_session)):
    item = require(db, MovementReason, reason_id)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return record(item, reason_fields)

@app.get('/api/responsibles', dependencies=auth)
def responsibles(db: Session = Depends(get_session)):
    return {'responsibles': [record(x, responsible_fields) for x in db.scalars(select(Responsible).order_by(Responsible.name, Responsible.employee_code))]}

@app.post('/api/responsibles', status_code=201, dependencies=auth)
def create_responsible(data: ResponsibleInput, db: Session = Depends(get_session)):
    item = Responsible(**data.model_dump())
    db.add(item)
    db.commit()
    return record(item, responsible_fields)

@app.put('/api/responsibles/{responsible_id}', dependencies=auth)
def update_responsible(responsible_id: int, data: ResponsibleInput, db: Session = Depends(get_session)):
    item = require(db, Responsible, responsible_id)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return record(item, responsible_fields)

recipient_company_fields = ['id', 'name', 'active']
recipient_fields = ['id', 'name', 'company_id', 'active']

@app.get('/api/recipient-companies', dependencies=auth)
def recipient_companies(db: Session = Depends(get_session)):
    return {'recipient_companies': [record(x, recipient_company_fields) for x in db.scalars(select(RecipientCompany).order_by(RecipientCompany.name))]}

@app.post('/api/recipient-companies', status_code=201, dependencies=auth)
def create_recipient_company(data: RecipientCompanyInput, db: Session = Depends(get_session)):
    item = RecipientCompany(**data.model_dump())
    db.add(item)
    db.commit()
    return record(item, recipient_company_fields)

@app.put('/api/recipient-companies/{company_id}', dependencies=auth)
def update_recipient_company(company_id: int, data: RecipientCompanyInput, db: Session = Depends(get_session)):
    item = require(db, RecipientCompany, company_id)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return record(item, recipient_company_fields)

@app.get('/api/recipients', dependencies=auth)
def recipients(db: Session = Depends(get_session)):
    return {'recipients': [record(x, recipient_fields) for x in db.scalars(select(Recipient).order_by(Recipient.name))]}

@app.post('/api/recipients', status_code=201, dependencies=auth)
def create_recipient(data: RecipientInput, db: Session = Depends(get_session)):
    if data.company_id:
        require(db, RecipientCompany, data.company_id)
    item = Recipient(**data.model_dump())
    db.add(item)
    db.commit()
    return record(item, recipient_fields)

@app.put('/api/recipients/{recipient_id}', dependencies=auth)
def update_recipient(recipient_id: int, data: RecipientInput, db: Session = Depends(get_session)):
    item = require(db, Recipient, recipient_id)
    if data.company_id:
        require(db, RecipientCompany, data.company_id)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return record(item, recipient_fields)

@app.get('/api/movements', dependencies=auth)
def movements(limit: int = 100, offset: int = 0, db: Session = Depends(get_session)):
    if not 1 <= limit <= 500 or offset < 0:
        raise HTTPException(422, 'Paginación inválida.')
    statement = select(StockMovement).order_by(StockMovement.id.desc()).limit(limit).offset(offset)
    return {'movements': [record(x, movement_fields) for x in db.scalars(statement)],
        'total': db.scalar(select(func.count()).select_from(StockMovement))}

@app.post('/api/movements', dependencies=auth)
def create_movement(data: MovementInput, db: Session = Depends(get_session)):
    # Lock the product even before its first balance exists. The ledger and balance
    # commit together; concurrent PostgreSQL requests cannot oversell the product.
    product = db.scalar(select(Product).where(Product.id == data.product_id).with_for_update())
    if product is None:
        raise HTTPException(404, 'Producto no encontrado.')
    require(db, Warehouse, data.warehouse_id)
    values = data.model_dump()
    values['request_id'] = str(data.request_id)
    existing = db.scalar(select(StockMovement).where(StockMovement.request_id == values['request_id']))
    if existing:
        if any(getattr(existing, key) != value for key, value in values.items()):
            raise HTTPException(409, 'Esta solicitud ya fue usada para otro movimiento.')
        return record(existing, movement_fields)
    reason = require(db, MovementReason, data.reason_id)
    responsible = require(db, Responsible, data.responsible_id)
    if not reason.active or not responsible.active:
        raise HTTPException(422, 'El motivo y el responsable deben estar activos.')
    if reason.kind not in ('both', data.kind):
        raise HTTPException(422, 'El motivo no corresponde al tipo de movimiento.')
    # Preserve the labels as they were when the movement was recorded.
    values['reason'] = reason.name
    values['operator'] = responsible.name
    if data.kind != 'exit' and (data.recipient_id is not None or data.reference):
        raise HTTPException(422, 'El retirante y el remito se registran solamente en salidas.')
    if data.recipient_id:
        recipient = require(db, Recipient, data.recipient_id)
        if not recipient.active:
            raise HTTPException(422, 'El retirante debe estar activo.')
        company = require(db, RecipientCompany, recipient.company_id) if recipient.company_id else require(db, Company, 1)
        if recipient.company_id and not company.active:
            raise HTTPException(422, 'La empresa del retirante debe estar activa.')
        values['recipient_name'] = recipient.name
        values['recipient_company'] = company.name

    balance = db.get(StockBalance, (data.product_id, data.warehouse_id))
    current = balance.quantity if balance else Decimal('0')
    result = current + data.quantity if data.kind == 'entry' else current - data.quantity
    if result < 0:
        raise HTTPException(409, 'Stock insuficiente en el depósito seleccionado.')
    if result >= Decimal('100000000000'):
        raise HTTPException(422, 'La cantidad total excede el máximo permitido.')
    if balance is None:
        balance = StockBalance(product_id=data.product_id, warehouse_id=data.warehouse_id)
        db.add(balance)
    balance.quantity = result
    movement = StockMovement(**values)
    db.add(movement)
    db.commit()
    return record(movement, movement_fields)
