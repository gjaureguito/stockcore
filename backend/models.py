from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from database import Base

class Company(Base):
    __tablename__ = 'companies'
    __table_args__ = (CheckConstraint('id = 1', name='single_company'),)
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)

class Warehouse(Base):
    __tablename__ = 'warehouses'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    address = Column(String(250), nullable=False, default='')

class Product(Base):
    __tablename__ = 'products'
    __table_args__ = (CheckConstraint('price >= 0', name='product_price_nonnegative'),)
    id = Column(Integer, primary_key=True)
    sku = Column(String(64), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='RESTRICT'))
    price = Column(Numeric(14, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class StockBalance(Base):
    __tablename__ = 'stock_balances'
    __table_args__ = (CheckConstraint('quantity >= 0', name='stock_nonnegative'),)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id', ondelete='RESTRICT'), primary_key=True)
    quantity = Column(Numeric(14, 3), nullable=False, default=0)

class StockMovement(Base):
    __tablename__ = 'stock_movements'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='movement_quantity_positive'),
        CheckConstraint("kind IN ('entry', 'exit')", name='movement_kind'),
        UniqueConstraint('request_id', name='movement_request_unique'),
    )
    id = Column(Integer, primary_key=True)
    request_id = Column(String(36), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True)
    kind = Column(String(10), nullable=False)
    quantity = Column(Numeric(14, 3), nullable=False)
    reason = Column(String(250), nullable=False)
    operator = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
