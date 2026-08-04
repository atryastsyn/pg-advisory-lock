import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError

from src.pg_advisory_lock.pg_local_setting import set_lock_timeout


def test_session_remains_usable_when_setting_lock_timeout_fails(session_factory):
    """A setting error inside a savepoint must not abort the outer transaction."""
    with session_factory() as session, session.begin():
        assert session.execute(text('SELECT 1')).scalar_one() == 1
        with pytest.raises(DataError) as exc_info, session.begin_nested(), set_lock_timeout(session, '-1ms'):
            pytest.fail('The context body should not be entered.')
        assert exc_info.value.orig.sqlstate == '22023'  # type: ignore
        assert session.execute(text('SELECT 2')).scalar_one() == 2
