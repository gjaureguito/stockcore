from alembic import context
from sqlalchemy import create_engine, pool
from database import Base, database_url
import models

def offline():
    context.configure(url=database_url(), target_metadata=Base.metadata, literal_binds=True, dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()

def online():
    existing = context.config.attributes.get('connection')
    if existing is not None:
        context.configure(connection=existing, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()

offline() if context.is_offline_mode() else online()
