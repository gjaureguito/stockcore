# StockCore API y base de datos

Primera versión para una empresa con varios depósitos. Incluye productos con SKU único,
categorías, depósitos, entradas, salidas, saldos por depósito e historial.

## Desarrollo en Windows

1. Iniciar PostgreSQL o `docker compose up -d db` desde la raíz.
2. Dentro de `backend`: `python -m venv .venv`, activar `.venv\Scripts\Activate.ps1` y
   `python -m pip install -r requirements.txt`.
3. Copiar `.env.example` a `.env`, configurar `DATABASE_URL`, `FRONTEND_URL` y una
   `STOCKCORE_API_KEY` propia. La clave permite entrar a la interfaz; nunca incluirla en el frontend compilado.
4. Ejecutar `python -m alembic upgrade head`. Crea las seis tablas y la empresa inicial.
5. Ejecutar `python -m uvicorn main:app --host 127.0.0.1 --port 8000`.
6. Dentro de `frontend`: `npm ci`, luego `npm start`. Abrir http://localhost:3000 e
   ingresar la clave configurada. Solo se conserva en memoria hasta salir o recargar.

La instancia preparada durante este trabajo utiliza el puerto **55432**, no 5432.
Los datos no se crean al importar ni iniciar la API: las migraciones se aplican explícitamente.

## Modelo

| Tabla | Uso |
|---|---|
| companies | Una empresa, id 1; nombre configurable |
| categories | Categorías con nombres únicos |
| warehouses | Depósitos con nombre y dirección |
| products | SKU único, nombre, categoría opcional y precio en ARS |
| stock_balances | Saldo único por producto y depósito, nunca negativo |
| stock_movements | Entradas/salidas, cantidad positiva, motivo, responsable y fecha |

Cantidades: decimal de tres posiciones. Precios: decimal de dos posiciones.
Los nuevos productos tienen stock cero; el inventario inicial se registra con entradas.
No se permite editar ni borrar movimientos; corregir con un movimiento compensatorio.
Las cantidades de stock no se editan directamente.

PostgreSQL bloquea la fila del producto durante cada movimiento; saldo e historial se
guardan en la misma transacción. `request_id` (UUID) evita duplicar el mismo movimiento
si se reintenta una solicitud. El reintento debe conservar el mismo identificador y contenido.

## API

Todas las rutas `/api/*` requieren `X-API-Key`. `/health` y `/` son públicas.
Sin `STOCKCORE_API_KEY` la API de negocio permanece deshabilitada.

| Rutas | Acciones |
|---|---|
| `/api/company` | GET, PUT nombre |
| `/api/categories` | GET, POST |
| `/api/warehouses` | GET, POST |
| `/api/products` | GET, POST |
| `/api/products/{id}` | PUT ficha de producto |
| `/api/stock?warehouse_id=1` | GET saldo por depósito (filtro opcional) |
| `/api/movements?limit=100&offset=0` | GET historial paginado, POST movimiento |
| `/api/ready` | GET comprueba conexión y tabla de empresa |

Documentación interactiva: http://localhost:8000/docs.

## Railway: preparación antes de publicar

No se aplicaron cambios a Railway ni a sus datos.

- Backend: conservar `DATABASE_URL` de Railway; configurar `STOCKCORE_API_KEY` con una clave de producción
  y `FRONTEND_URL=https://stock.jaureguitosistemas.com` (admite varios orígenes separados por coma).
- Crear un respaldo de la base de producción antes de migrarla.
- Configurar un paso de pre-despliegue: `python -m alembic upgrade head` dentro de `backend`.
- Mantener `uvicorn main:app --host 0.0.0.0 --port $PORT` y healthcheck `/health`.
- Frontend: `REACT_APP_API_URL=https://backend-production-1a6e5.up.railway.app`.
- Nunca configurar la clave de acceso como variable `REACT_APP_*`: sería pública en el navegador.

Esta primera versión usa una clave compartida y un responsable escrito en cada movimiento.
No implementa cuentas individuales, roles ni identidad auditada. Tampoco implementa compras,
ventas, transferencias entre depósitos ni conexión contable. El precio usa ARS.

## Pruebas

`python -m pip install -r requirements-dev.txt` y `python -m pytest tests -q`.
Sin `TEST_DATABASE_URL` prueba reglas y migraciones en SQLite; omite dos pruebas de concurrencia.
Para las cuatro pruebas usar una base PostgreSQL **vacía y descartable**:
`$env:TEST_DATABASE_URL='postgresql://usuario:clave@localhost:55432/stockcore_test'`.
Las pruebas crean y eliminan exclusivamente las tablas de esa base al terminar cada caso.
No usar la base de desarrollo ni producción para esta variable.

Para nuevas migraciones: `python -m alembic revision --autogenerate -m "descripcion"`,
revisar el resultado y ejecutar `python -m alembic upgrade head`.
