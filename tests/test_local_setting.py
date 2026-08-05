import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError

from pg_advisory_lock.pg_local_setting import pg_get_local_setting, pg_set_local_setting, set_lock_timeout


def test_session_remains_usable_when_setting_lock_timeout_fails(db_session):
    """A setting error inside a savepoint must not abort the outer transaction."""
    assert db_session.execute(text('SELECT 1')).scalar_one() == 1
    with pytest.raises(DataError) as exc_info, db_session.begin_nested(), set_lock_timeout(db_session, '-1ms'):
        pytest.fail('The context body should not be entered.')
    assert exc_info.value.orig.sqlstate == '22023'  # type: ignore
    assert db_session.execute(text('SELECT 2')).scalar_one() == 2


@pytest.mark.parametrize(
    argnames='setting_name,initial_setting_value,updated_setting_value',
    argvalues=[
        ('lock_timeout', '275ms', '100ms'),
        ('statement_timeout', '5s', '500ms'),
    ],
)
def test_local_setting_restores_its_initial_value(
    setting_name, initial_setting_value, updated_setting_value, db_session
):
    db_session.execute(
        statement=text('SELECT set_config(:name, :value, TRUE)'),
        params={'name': setting_name, 'value': initial_setting_value},
    )

    with pg_set_local_setting(session=db_session, name=setting_name, value=updated_setting_value):
        result = db_session.execute(
            statement=text('SELECT pg_try_advisory_xact_lock(:key);'),
            params={'key': 123},
        ).scalar()
        db_session.execute(statement=text('SELECT 1;'))
        assert result is True

    assert pg_get_local_setting(session=db_session, name=setting_name) == initial_setting_value
