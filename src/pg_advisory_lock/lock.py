from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from .exceptions import PgAdvisoryLockError, PgAdvisoryLockNotAcquired, PgAdvisoryLockTimeout, lock_is_not_available
from .lock_arguments import get_key_from_args, validate
from .pg_local_setting import set_lock_timeout


class PGAdvisoryLock:
    def __init__(self, lock_args: list[Any] | tuple[Any, ...], raise_on_failure: bool = True):
        self.raise_on_failure = raise_on_failure

        if not isinstance(lock_args, (list, tuple)):
            raise PgAdvisoryLockError('Lock arguments must be a list or tuple.')
        self.lock_args = tuple(lock_args)
        validate(self.lock_args)

        self.lock_key = get_key_from_args(self.lock_args)

    def lock_immediate(self, session: Session) -> bool:
        result = session.execute(
            statement=text('SELECT pg_try_advisory_xact_lock(:key)'),
            params={'key': self.lock_key},
        ).scalar()
        if result:
            return True
        else:
            if self.raise_on_failure:
                raise PgAdvisoryLockNotAcquired('Failed to acquire advisory lock.')
            else:
                return False

    def lock(self, session: Session, timeout_in_ms: int = 1000) -> bool:
        if not isinstance(timeout_in_ms, int) or timeout_in_ms < 0:
            raise PgAdvisoryLockError('Lock timeout must be a non-negative integer.')

        if timeout_in_ms == 0:
            return self.lock_immediate(session=session)

        try:
            with session.begin_nested(), set_lock_timeout(session, f'{timeout_in_ms}ms'):
                session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': self.lock_key})
                return True

        except DBAPIError as exc:
            if not lock_is_not_available(error=exc):
                raise

            elif self.raise_on_failure:
                raise PgAdvisoryLockTimeout(
                    f'Failed to acquire advisory lock within {timeout_in_ms} ms.',
                ) from exc

            else:
                return False
