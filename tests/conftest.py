import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_URL = 'postgresql+psycopg://postgres:123@localhost:6543/'


@pytest.fixture
def engine_factory():
    engine = create_engine(DB_URL)

    yield engine

    engine.dispose()


@pytest.fixture
def session_factory(engine_factory):
    return sessionmaker(bind=engine_factory)
