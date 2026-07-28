from src.pg_advisory_lock.lock_arguments import get_key_from_args


def test_get_key_from_args_deterministic_same_args():
    key1 = get_key_from_args(('user_sync', 'RU', 123))
    key2 = get_key_from_args(('user_sync', 'RU', 123))
    assert key1 == key2


def test_get_key_from_args_different_for_different_args():
    key1 = get_key_from_args(('user_sync', 'RU', 123))
    key2 = get_key_from_args(('user_sync', 'US', 123))
    assert key1 != key2
