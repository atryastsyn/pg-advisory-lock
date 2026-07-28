import logging
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.exc import InternalError
from sqlalchemy.orm import Session

IN_FAILED_SQL_TRANSACTION = '25P02'


def pg_reset_local_setting(session: Session, name: str):
    try:
        session.execute(text(f'SET LOCAL {name} = DEFAULT'))
    except InternalError as e:
        pgcode = getattr(e.orig, 'pgcode', None)
        if pgcode == IN_FAILED_SQL_TRANSACTION:
            logging.info('Lock acquisition skiper for an already failed transaction.', exc_info=e)
        else:
            raise


@contextmanager
def pg_set_local_setting(session: Session, name: str, timeout: int | str):
    session.execute(text(f'SET LOCAL {name} = :val'), {'val': str(timeout)})
    try:
        yield
    finally:
        pg_reset_local_setting(session=session, name=name)


def set_lock_timeout(session: Session, timeout: int | str):
    setting_name = 'lock_timeout'
    return pg_set_local_setting(session=session, name=setting_name, timeout=timeout)
