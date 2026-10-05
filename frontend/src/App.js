import React, { useState } from 'react';
import './App.css';
import api, { errorMessage, setAccessKey } from './api';

const emptyProduct = { name: '', sku: '', price: '', category_id: '' };
const emptyMovement = () => ({ product_id: '', warehouse_id: '', kind: 'entry', quantity: '', reason: '', operator: '', request_id: crypto.randomUUID() });

function App() {
  const [access, setAccess] = useState('');
  const [connected, setConnected] = useState(false);
  const [tab, setTab] = useState('Productos');
  const [data, setData] = useState({ products: [], categories: [], warehouses: [], stock: [], movements: [], company: { name: '' }, total: 0 });
  const [product, setProduct] = useState(emptyProduct);
  const [movement, setMovement] = useState(emptyMovement);
  const [category, setCategory] = useState('');
  const [warehouse, setWarehouse] = useState({ name: '', address: '' });
  const [companyName, setCompanyName] = useState('');
  const [filter, setFilter] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load() {
    const results = await Promise.all(['/api/products', '/api/categories', '/api/warehouses', '/api/stock', '/api/movements', '/api/company'].map(path => api.get(path)));
    setData({ ...results[0].data, ...results[1].data, ...results[2].data, ...results[3].data,
      movements: results[4].data.movements, total: results[4].data.total, company: results[5].data });
    setCompanyName(results[5].data.name);
  }
  async function connect(e) {
    e.preventDefault(); setBusy(true); setError(''); setAccessKey(access);
    try { await load(); setConnected(true); setAccess(''); }
    catch (err) { setError(errorMessage(err)); setAccessKey(''); }
    finally { setBusy(false); }
  }
  async function save(e, path, payload, reset, method = 'post') {
    e.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      await api[method](path, payload); reset(); setNotice('Guardado correctamente.');
      try { await load(); } catch (err) { setError('Se guardó, pero no se pudo actualizar la vista. Usá Actualizar.'); }
    } catch (err) { setError(errorMessage(err)); }
    finally { setBusy(false); }
  }
  async function refresh() {
    setBusy(true); setError('');
    try { await load(); } catch (err) { setError(errorMessage(err)); }
    finally { setBusy(false); }
  }
  function disconnect() { setAccessKey(''); setConnected(false); setData({ products: [], categories: [], warehouses: [], stock: [], movements: [], company: { name: '' }, total: 0 }); setError(''); setNotice(''); }
  const productName = id => data.products.find(p => p.id === id)?.name || id;
  const warehouseName = id => data.warehouses.find(w => w.id === id)?.name || id;
  const money = value => Number(value).toLocaleString('es-AR', { style: 'currency', currency: 'ARS' });
  const filtered = data.products.filter(p => `${p.name} ${p.sku}`.toLowerCase().includes(filter.toLowerCase()));

  if (!connected) return <main className="login"><h1>StockCore</h1><p>Gestión de inventario para tu empresa</p>
    <form onSubmit={connect}><label>Clave de acceso<input disabled={busy} type="password" autoComplete="off" required value={access} onChange={e => setAccess(e.target.value)} /></label><button disabled={busy}>{busy ? 'Conectando…' : 'Ingresar'}</button></form>
    {error && <p className="error" role="alert">{error}</p>}</main>;

  return <div className="container"><header><div><span className="brand">StockCore</span><h1>{data.company.name}</h1><p>Productos y existencias en cada depósito</p></div><button className="secondary" onClick={disconnect} disabled={busy}>Salir</button></header>
    <section className="summary" aria-label="Resumen"><div><strong>{data.products.length}</strong>Productos</div><div><strong>{data.warehouses.length}</strong>Depósitos</div><div><strong>{data.total}</strong>Movimientos</div></section>
    <nav aria-label="Secciones">{['Productos', 'Movimientos', 'Stock por depósito', 'Configuración'].map(name => <button key={name} className={tab === name ? 'active' : 'secondary'} onClick={() => setTab(name)}>{name}</button>)}<button className="secondary" onClick={refresh} disabled={busy}>Actualizar</button></nav>
    {error && <p role="alert" className="error">{error}</p>}{notice && <p role="status" className="notice">{notice}</p>}
    {tab === 'Productos' && <div className="content"><section className="panel"><h2>Nuevo producto</h2><form onSubmit={e => save(e, '/api/products', { ...product, price: product.price || '0', category_id: product.category_id ? Number(product.category_id) : null }, () => setProduct(emptyProduct))}>
      <label>Código / SKU<input disabled={busy} required maxLength={64} value={product.sku} onChange={e => setProduct({ ...product, sku: e.target.value })} /></label>
      <label>Nombre<input disabled={busy} required maxLength={120} value={product.name} onChange={e => setProduct({ ...product, name: e.target.value })} /></label>
      <label>Categoría<select disabled={busy} value={product.category_id} onChange={e => setProduct({ ...product, category_id: e.target.value })}><option value="">Sin categoría</option>{data.categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
      <label>Precio (ARS)<input disabled={busy} type="number" min="0" step="0.01" value={product.price} onChange={e => setProduct({ ...product, price: e.target.value })} /></label><p className="muted">El stock inicial se registra como una entrada en Movimientos.</p><button disabled={busy}>Crear producto</button></form></section>
      <section className="panel"><h2>Productos</h2><label>Buscar<input disabled={busy} value={filter} onChange={e => setFilter(e.target.value)} placeholder="Nombre o código" /></label><div className="table-wrap"><table><thead><tr><th>Código</th><th>Producto</th><th>Categoría</th><th>Stock total</th><th>Precio</th></tr></thead><tbody>{filtered.map(p => <tr key={p.id}><td>{p.sku}</td><td>{p.name}</td><td>{data.categories.find(c => c.id === p.category_id)?.name || '—'}</td><td>{Number(p.quantity)}</td><td>{money(p.price)}</td></tr>)}</tbody></table></div>{!filtered.length && <p className="muted">No hay productos para mostrar.</p>}</section></div>}
    {tab === 'Movimientos' && <div className="content"><section className="panel"><h2>Registrar movimiento</h2><form onSubmit={e => save(e, '/api/movements', { ...movement, product_id: Number(movement.product_id), warehouse_id: Number(movement.warehouse_id) }, () => setMovement(emptyMovement()))}>
      <label>Producto<select disabled={busy} required value={movement.product_id} onChange={e => setMovement({ ...movement, product_id: e.target.value, request_id: crypto.randomUUID() })}><option value="">Seleccionar producto</option>{data.products.map(p => <option key={p.id} value={p.id}>{p.sku} · {p.name}</option>)}</select></label>
      <label>Depósito<select disabled={busy} required value={movement.warehouse_id} onChange={e => setMovement({ ...movement, warehouse_id: e.target.value, request_id: crypto.randomUUID() })}><option value="">Seleccionar depósito</option>{data.warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
      <label>Tipo<select disabled={busy} value={movement.kind} onChange={e => setMovement({ ...movement, kind: e.target.value, request_id: crypto.randomUUID() })}><option value="entry">Entrada</option><option value="exit">Salida</option></select></label>
      <label>Cantidad<input disabled={busy} required type="number" min="0.001" step="0.001" value={movement.quantity} onChange={e => setMovement({ ...movement, quantity: e.target.value, request_id: crypto.randomUUID() })} /></label>
      <label>Motivo<input disabled={busy} required maxLength={250} value={movement.reason} onChange={e => setMovement({ ...movement, reason: e.target.value, request_id: crypto.randomUUID() })} /></label>
      <label>Responsable<input disabled={busy} required maxLength={120} value={movement.operator} onChange={e => setMovement({ ...movement, operator: e.target.value, request_id: crypto.randomUUID() })} /></label>
      <button disabled={busy || !data.products.length || !data.warehouses.length}>Registrar {movement.kind === 'entry' ? 'entrada' : 'salida'}</button>{(!data.products.length || !data.warehouses.length) && <p className="muted">Creá un producto y un depósito antes de registrar movimientos.</p>}</form></section>
      <section className="panel"><h2>Últimos movimientos</h2><p className="muted">Se muestran los últimos 100 de {data.total} movimientos.</p><div className="table-wrap"><table><thead><tr><th>Fecha</th><th>Producto / depósito</th><th>Tipo</th><th>Cantidad</th><th>Motivo / responsable</th></tr></thead><tbody>{data.movements.map(m => <tr key={m.id}><td>{new Date(m.created_at).toLocaleString('es-AR')}</td><td>{productName(m.product_id)}<small>{warehouseName(m.warehouse_id)}</small></td><td><span className={`badge ${m.kind}`}>{m.kind === 'entry' ? 'Entrada' : 'Salida'}</span></td><td>{Number(m.quantity)}</td><td>{m.reason}<small>{m.operator}</small></td></tr>)}</tbody></table></div>{!data.movements.length && <p className="muted">Todavía no hay movimientos.</p>}</section></div>}
    {tab === 'Stock por depósito' && <section className="panel"><h2>Existencias</h2><div className="table-wrap"><table><thead><tr><th>Depósito</th><th>Código</th><th>Producto</th><th>Cantidad</th></tr></thead><tbody>{data.stock.map(s => <tr key={`${s.product_id}-${s.warehouse_id}`}><td>{s.warehouse}</td><td>{s.sku}</td><td>{s.product}</td><td>{Number(s.quantity)}</td></tr>)}</tbody></table></div>{!data.stock.length && <p className="muted">Registrá una entrada para comenzar a consultar existencias.</p>}</section>}
    {tab === 'Configuración' && <div className="settings"><section className="panel"><h2>Empresa</h2><form onSubmit={e => save(e, '/api/company', { name: companyName }, () => {}, 'put')}><label>Nombre<input disabled={busy} required maxLength={120} value={companyName} onChange={e => setCompanyName(e.target.value)} /></label><button disabled={busy}>Guardar nombre</button></form></section>
      <section className="panel"><h2>Categorías</h2><form onSubmit={e => save(e, '/api/categories', { name: category }, () => setCategory(''))}><label>Nombre<input disabled={busy} required maxLength={120} value={category} onChange={e => setCategory(e.target.value)} /></label><button disabled={busy}>Crear categoría</button></form><ul>{data.categories.map(c => <li key={c.id}>{c.name}</li>)}</ul></section>
      <section className="panel"><h2>Depósitos</h2><form onSubmit={e => save(e, '/api/warehouses', warehouse, () => setWarehouse({ name: '', address: '' }))}><label>Nombre<input disabled={busy} required maxLength={120} value={warehouse.name} onChange={e => setWarehouse({ ...warehouse, name: e.target.value })} /></label><label>Dirección<input disabled={busy} maxLength={250} value={warehouse.address} onChange={e => setWarehouse({ ...warehouse, address: e.target.value })} /></label><button disabled={busy}>Crear depósito</button></form><ul>{data.warehouses.map(w => <li key={w.id}>{w.name}<small>{w.address}</small></li>)}</ul></section></div>}
  </div>;
}
export default App;

