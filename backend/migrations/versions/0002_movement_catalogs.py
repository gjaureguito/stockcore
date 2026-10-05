"""Typed reasons and responsibles; preserve historical movement labels."""
from alembic import op
import sqlalchemy as sa
revision = '0002_movement_catalogs'
down_revision = '0001_inventory'
branch_labels = None
depends_on = None

def upgrade():
    reasons = op.create_table('movement_reasons',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), unique=True, nullable=False),
        sa.Column('kind', sa.String(10), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.CheckConstraint("kind IN ('entry', 'exit', 'both')", name='reason_kind'))
    op.create_table('responsibles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('employee_code', sa.String(64), unique=True, nullable=False),
        sa.Column('sector', sa.String(120), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False))
    with op.batch_alter_table('stock_movements') as batch:
        batch.add_column(sa.Column('reason_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('responsible_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('movement_reason_fk', 'movement_reasons', ['reason_id'], ['id'], ondelete='RESTRICT')
        batch.create_foreign_key('movement_responsible_fk', 'responsibles', ['responsible_id'], ['id'], ondelete='RESTRICT')
    op.bulk_insert(reasons, [{'name': name, 'kind': kind, 'active': True} for name, kind in [
        ('Compra', 'entry'), ('Devolución', 'entry'), ('Stock inicial', 'entry'),
        ('Consumo en operación', 'exit'), ('Entrega a personal', 'exit'),
        ('Rotura', 'exit'), ('Pérdida', 'exit'), ('Ajuste de inventario', 'both')]])

def downgrade():
    with op.batch_alter_table('stock_movements') as batch:
        batch.drop_constraint('movement_responsible_fk', type_='foreignkey')
        batch.drop_constraint('movement_reason_fk', type_='foreignkey')
        batch.drop_column('responsible_id')
        batch.drop_column('reason_id')
    op.drop_table('responsibles')
    op.drop_table('movement_reasons')
