from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session


@contextmanager
def pg_set_local_setting(session: Session, name: str, value: int | str):
    session.execute(text('SELECT set_config(:name, :value, TRUE)'), {'name': name, 'value': value})

    yield

    session.execute(text(f'SET LOCAL {name} = DEFAULT'))


def set_lock_timeout(session: Session, timeout: int | str):
    setting_name = 'lock_timeout'
    return pg_set_local_setting(session=session, name=setting_name, value=timeout)
