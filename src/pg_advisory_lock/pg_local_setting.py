from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session


def pg_get_local_setting(session: Session, name: str) -> str:
    result = session.execute(statement=text('SELECT current_setting(:name)'), params={'name': name}).scalar_one()
    return str(result)


@contextmanager
def pg_set_local_setting(session: Session, name: str, value: str) -> Generator[None]:
    # Get the current value
    current_value = pg_get_local_setting(session=session, name=name)

    # Set the new value
    session.execute(text('SELECT set_config(:name, :value, TRUE)'), {'name': name, 'value': value})

    yield

    # Restore initial value
    session.execute(text('SELECT set_config(:name, :value, TRUE)'), {'name': name, 'value': current_value})


def set_lock_timeout(session: Session, timeout: str) -> AbstractContextManager[None]:
    setting_name = 'lock_timeout'
    return pg_set_local_setting(session=session, name=setting_name, value=timeout)
