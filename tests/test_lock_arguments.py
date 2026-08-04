from decimal import Decimal

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

from src.pg_advisory_lock import PGAdvisoryLock, PgAdvisoryLockError
from src.pg_advisory_lock.lock_arguments import get_key_from_args, normalize, validate


class Base(DeclarativeBase): ...


class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)


def test_get_key_from_args_deterministic_same_args():
    key1 = get_key_from_args(('user_sync', 'RU', 123))
    key2 = get_key_from_args(('user_sync', 'RU', 123))
    assert key1 == key2


def test_get_key_from_args_different_for_different_args():
    key1 = get_key_from_args(('user_sync', 'RU', 123))
    key2 = get_key_from_args(('user_sync', 'US', 123))
    assert key1 != key2


def test_get_key_from_args_order_matters():
    key1 = get_key_from_args(('A', 'B', 'C'))
    key2 = get_key_from_args(('C', 'B', 'A'))
    assert key1 != key2


@pytest.mark.parametrize(
    argnames='lock_args, expected_exception, exception_message',
    argvalues=[
        ((1, 2, 3), None, None),
        (tuple(), PgAdvisoryLockError, 'At least one lock argument is required.'),
        ((None, 2, 3), PgAdvisoryLockError, 'Lock argument can not be "None".'),
    ],
    ids=['No Exception', 'Empty lock arguments list', 'None is not allowed'],
)
def test_validate(lock_args, expected_exception, exception_message):
    if expected_exception:
        with pytest.raises(expected_exception=expected_exception, match=exception_message):
            validate(args=lock_args)
    else:
        validate(args=lock_args)


def test_normalize_model():
    user_model = UserModel(id=1, first_name='Alex', last_name='Tryastsyn')
    assert normalize(arg=user_model) == user_model.__tablename__


def test_normalize_table(test_table):
    assert normalize(arg=test_table) == test_table.name


@pytest.mark.parametrize(
    argnames='lock_arg, result',
    argvalues=[('1', '1'), (1, '1'), (None, 'None'), (True, 'True'), (Decimal('1.1'), '1.1')],
)
def test_normalize_other_types(lock_arg, result):
    assert normalize(arg=lock_arg) == result


@pytest.mark.parametrize(
    'lock_args',
    [
        'payment',
        {'payment'},
        {'payment': 1},
        (value for value in ['payment']),
        None,
    ],
)
def test_lock_rejects_non_list_or_tuple_arguments(lock_args):
    with pytest.raises(
        PgAdvisoryLockError,
        match='Lock arguments must be a list or tuple.',
    ):
        PGAdvisoryLock(lock_args)


def test_lock_copies_arguments_to_immutable_tuple():
    lock_args = ['payment']
    lock = PGAdvisoryLock(lock_args)

    lock_args.append(123)  # type: ignore

    assert lock.lock_args == ('payment',)


def test_get_key_from_args_distinguishes_component_boundaries():
    first_key = get_key_from_args(('a:b', 'c'))
    second_key = get_key_from_args(('a', 'b:c'))

    assert first_key != second_key


def test_get_key_from_args_matches_stable_key():
    assert get_key_from_args(('user_sync', 'RU', 123)) == 4110131889271348223


def test_get_key_from_args_normalizes_equivalent_values():
    assert get_key_from_args((1,)) == get_key_from_args(('1',))
