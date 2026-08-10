from decimal import Decimal

import pytest

from pg_advisory_lock import PgAdvisoryLock, PgAdvisoryLockError
from pg_advisory_lock.lock_arguments import LOCK_ARGUMENT_TYPE_NAMES, get_key_from_args, normalize, validate


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
        ([1, 2, 3], None, None),
        ({1, 2, 3}, PgAdvisoryLockError, 'Lock arguments must be a list or tuple.'),
        ({'1': 2}, PgAdvisoryLockError, 'Lock arguments must be a list or tuple.'),
        (tuple(), PgAdvisoryLockError, 'At least one lock argument is required.'),
        ((None, 2, 3), PgAdvisoryLockError, 'Lock argument can not be "None".'),
        (
            (Decimal('1.0'),),
            PgAdvisoryLockError,
            f'Lock argument must be one of "{LOCK_ARGUMENT_TYPE_NAMES}", got "Decimal" instead.',
        ),
        (
            (object(),),
            PgAdvisoryLockError,
            f'Lock argument must be one of "{LOCK_ARGUMENT_TYPE_NAMES}", got "object" instead.',
        ),
        (
            (float(1),),
            PgAdvisoryLockError,
            f'Lock argument must be one of "{LOCK_ARGUMENT_TYPE_NAMES}", got "float" instead.',
        ),
    ],
    ids=[
        'Tuples are allowed, no exception',
        'Lists are allowed, no exception',
        'Sets are not allowed',
        'Dicts are not allowed',
        'Empty list is not allowed',
        'None entry is not allowed',
        'Decimal entry is not allowed',
        'Object entry is not allowed',
        'Float entry is not allowed',
    ],
)
def test_validate(lock_args, expected_exception, exception_message):
    if expected_exception:
        with pytest.raises(expected_exception=expected_exception, match=exception_message):
            validate(args=lock_args)
    else:
        validate(args=lock_args)


@pytest.mark.parametrize(
    argnames='lock_arg, result',
    argvalues=[('1', '1'), (1, '1'), (None, 'None'), (True, 'True'), (Decimal('1.1'), '1.1')],
)
def test_normalize_other_types(lock_arg, result):
    assert normalize(arg=lock_arg) == result


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=[None, 1, 'True', (False,), {True}, {'False': True}])
def test_lock_rejects_non_bool_raise_on_failure(raise_on_failure):
    with pytest.raises(PgAdvisoryLockError):
        PgAdvisoryLock(lock_args=(1, 2, 3), raise_on_failure=raise_on_failure)


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
        PgAdvisoryLock(lock_args)


def test_lock_copies_arguments_to_immutable_tuple():
    lock_args = ['payment']
    lock = PgAdvisoryLock(lock_args)

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
