"""Initial single-company inventory schema. Frozen definitions for reproducibility."""
from alembic import op
import sqlalchemy as sa

revision = '0001_inventory'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    companies = op.create_table('companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.CheckConstraint('id = 1', name='single_company'))
    op.create_table('categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False, unique=True))
    op.create_table('warehouses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False, unique=True),
        sa.Column('address', sa.String(250), nullable=False))
    op.create_table('products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sku', sa.String(64), nullable=False, unique=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='RESTRICT')),
        sa.Column('price', sa.Numeric(14, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('price >= 0', name='product_price_nonnegative'))
    op.create_table('stock_balances',
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True),
        sa.Column('warehouse_id', sa.Integer(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), primary_key=True),
        sa.Column('quantity', sa.Numeric(14, 3), nullable=False),
        sa.CheckConstraint('quantity >= 0', name='stock_nonnegative'))
    op.create_table('stock_movements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('request_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('kind', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Numeric(14, 3), nullable=False),
        sa.Column('reason', sa.String(250), nullable=False),
        sa.Column('operator', sa.String(120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('request_id', name='movement_request_unique'),
        sa.CheckConstraint('quantity > 0', name='movement_quantity_positive'),
        sa.CheckConstraint("kind IN ('entry', 'exit')", name='movement_kind'))
    op.create_index('ix_stock_movements_product_id', 'stock_movements', ['product_id'])
    op.create_index('ix_stock_movements_warehouse_id', 'stock_movements', ['warehouse_id'])
    op.bulk_insert(companies, [{'id': 1, 'name': 'Mi empresa'}])

def downgrade():
    for name in ['stock_movements', 'stock_balances', 'products', 'warehouses', 'categories', 'companies']:
        op.drop_table(name)
