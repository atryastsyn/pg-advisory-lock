import os

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql+psycopg://postgres:123@localhost:6543/testing',
)


@pytest.fixture(scope='session')
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope='session')
def session_factory(engine):
    return sessionmaker(bind=engine)


@pytest.fixture
def db_session(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture
def test_table() -> Table:
    metadata = MetaData()
    return Table(
        'test_items',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False),
    )
