import axios from 'axios';

const configured = process.env.REACT_APP_API_URL || 'http://localhost:8000';
// Accept the legacy Railway hostname while configuration is corrected.
const baseURL = /^https?:\/\//i.test(configured) ? configured : `https://${configured}`;
const api = axios.create({ baseURL, timeout: 15000 });
export function setAccessKey(key) {
  if (key) api.defaults.headers.common['X-API-Key'] = key;
  else delete api.defaults.headers.common['X-API-Key'];
}
export function errorMessage(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return 'Revisá los campos: códigos, cantidades y precios deben ser válidos.';
  return error.response ? 'No se pudo completar la operación.' : 'No se pudo conectar con el servidor. Revisá la conexión y volvé a intentar.';
}
export default api;
