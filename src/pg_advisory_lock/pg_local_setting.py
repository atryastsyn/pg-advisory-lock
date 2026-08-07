"""Helpers for reading and temporarily overriding transaction-local PostgreSQL settings."""

from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session


def pg_get_local_setting(session: Session, name: str) -> str:
    """Read the session's effective value for a PostgreSQL run-time setting.

    PostgreSQL errors on an unrecognized setting name, so the caller must pass one that exists in
    the server configuration.
    """

    result = session.execute(statement=text('SELECT current_setting(:name)'), params={'name': name}).scalar_one()
    return str(result)


@contextmanager
def pg_set_local_setting(session: Session, name: str, value: str) -> Generator[None]:
    """Override a transaction-local PostgreSQL setting for the duration of the block.

    The override uses SET LOCAL semantics, so it is scoped to the current transaction or savepoint
    and never affects other sessions. On normal exit the captured previous value is written back
    explicitly. If the block raises, that restore is skipped and the caller's transaction or
    savepoint rollback is what undoes the override.
    """

    current_value = pg_get_local_setting(session=session, name=name)

    session.execute(text('SELECT set_config(:name, :value, TRUE)'), {'name': name, 'value': value})

    yield

    session.execute(text('SELECT set_config(:name, :value, TRUE)'), {'name': name, 'value': current_value})


def set_lock_timeout(session: Session, timeout: str) -> AbstractContextManager[None]:
    """Override lock_timeout for the block, using a PostgreSQL interval string such as '1000ms'."""

    setting_name = 'lock_timeout'
    return pg_set_local_setting(session=session, name=setting_name, value=timeout)
