"""Recipients and external companies; retain historical snapshots."""
from alembic import op
import sqlalchemy as sa
revision = '0003_recipients'
down_revision = '0002_movement_catalogs'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('recipient_companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), unique=True, nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False))
    op.create_table('recipients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('recipient_companies.id', ondelete='RESTRICT')),
        sa.Column('active', sa.Boolean(), nullable=False))
    with op.batch_alter_table('stock_movements') as batch:
        batch.add_column(sa.Column('recipient_id', sa.Integer()))
        batch.add_column(sa.Column('recipient_name', sa.String(120)))
        batch.add_column(sa.Column('recipient_company', sa.String(120)))
        batch.add_column(sa.Column('reference', sa.String(120), nullable=False, server_default=''))
        batch.create_foreign_key('movement_recipient_fk', 'recipients', ['recipient_id'], ['id'], ondelete='RESTRICT')

def downgrade():
    with op.batch_alter_table('stock_movements') as batch:
        batch.drop_constraint('movement_recipient_fk', type_='foreignkey')
        for name in ['reference', 'recipient_company', 'recipient_name', 'recipient_id']:
            batch.drop_column(name)
    op.drop_table('recipients')
    op.drop_table('recipient_companies')
