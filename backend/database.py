import os
from functools import lru_cache
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

class Base(DeclarativeBase):
    pass

def database_url():
    url = os.getenv('DATABASE_URL')
    if not url:
        raise RuntimeError('Configure DATABASE_URL para conectar PostgreSQL.')
    return 'postgresql://' + url[11:] if url.startswith('postgres://') else url

@lru_cache
def session_factory():
    return sessionmaker(create_engine(database_url(), pool_pre_ping=True), expire_on_commit=False)

def get_session():
    with session_factory()() as session:
        yield session
