import logging
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.exc import InternalError
from sqlalchemy.orm import Session

from .exceptions import PgAdvisoryLockError

IN_FAILED_SQL_TRANSACTION = '25P02'

ALLOWED_SETTINGS = {'lock_timeout', 'statement_timeout'}


def pg_reset_local_setting(db_session: Session, name: str):
    if name not in ALLOWED_SETTINGS:
        raise PgAdvisoryLockError(f'Setting name "{name}" is not allowed')

    try:
        db_session.execute(text(f'SET LOCAL {name} = DEFAULT'))
    except InternalError as e:
        pgcode = getattr(e.orig, 'pgcode', None)
        if pgcode == IN_FAILED_SQL_TRANSACTION:
            logging.info('Lock acquisition skiper for an already failed transaction.', exc_info=e)
        else:
            raise


@contextmanager
def pg_set_local_setting(db_session: Session, name: str, timeout: int | str):
    if name not in ALLOWED_SETTINGS:
        raise PgAdvisoryLockError(f'Setting name "{name}" is not allowed')

    db_session.execute(text(f'SET LOCAL {name} = :val'), {'val': str(timeout)})
    try:
        yield
    finally:
        pg_reset_local_setting(db_session=db_session, name=name)
