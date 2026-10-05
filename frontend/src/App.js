import React, { useState, useEffect } from 'react';
import './App.css';
import api from './api';

function App() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newProduct, setNewProduct] = useState({ name: '', quantity: '', price: '' });

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/products');
      setProducts(response.data.products || []);
    } catch (err) {
      setError('Error al cargar productos: ' + (err.message || 'Error desconocido'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddProduct = async (e) => {
    e.preventDefault();
    if (!newProduct.name.trim()) return;
    
    try {
      await api.post('/api/products', newProduct);
      setNewProduct({ name: '', quantity: '', price: '' });
      fetchProducts();
    } catch (err) {
      setError('Error al agregar producto: ' + (err.message || 'Error desconocido'));
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>📦 StockCore</h1>
        <p>Sistema de Gestión de Inventario</p>
      </header>

      <div className="content">
        <section className="form-section">
          <h2>Agregar Producto</h2>
          <form onSubmit={handleAddProduct}>
            <input
              type="text"
              placeholder="Nombre del producto"
              value={newProduct.name}
              onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
              required
            />
            <input
              type="number"
              placeholder="Cantidad"
              value={newProduct.quantity}
              onChange={(e) => setNewProduct({ ...newProduct, quantity: e.target.value })}
            />
            <input
              type="number"
              placeholder="Precio"
              value={newProduct.price}
              onChange={(e) => setNewProduct({ ...newProduct, price: e.target.value })}
              step="0.01"
            />
            <button type="submit">Agregar</button>
          </form>
        </section>

        <section className="products-section">
          <h2>Productos ({products.length})</h2>
          {loading && <p className="info">Cargando...</p>}
          {error && <p className="error">{error}</p>}
          {!loading && products.length === 0 && <p className="info">No hay productos aún.</p>}
          {!loading && products.length > 0 && (
            <table className="products-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Cantidad</th>
                  <th>Precio</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product, idx) => (
                  <tr key={idx}>
                    <td>{product.name}</td>
                    <td>{product.quantity}</td>
                    <td>${product.price}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </div>
  );
}

export default App;

