from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="StockCore API", version="0.1.0")

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "stockcore-api"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "StockCore API", "version": "0.1.0"}

@app.get("/api/products")
async def get_products():
    """Get all products (placeholder)"""
    return {"products": [], "total": 0}

@app.post("/api/products")
async def create_product(product: dict):
    """Create a new product (placeholder)"""
    return {"message": "Product created", "product": product}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

