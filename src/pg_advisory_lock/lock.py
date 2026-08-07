"""Transaction-scoped PostgreSQL advisory locks acquired through a SQLAlchemy session."""

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from .exceptions import PgAdvisoryLockError, PgAdvisoryLockNotAcquired, PgAdvisoryLockTimeout, lock_is_not_available
from .lock_arguments import get_key_from_args, validate
from .pg_local_setting import set_lock_timeout


class PgAdvisoryLock:
    """Advisory lock addressed by a key derived from structured lock arguments.

    The key is derived once at construction, so invalid arguments fail before any database call.
    Acquisition is transaction-scoped: PostgreSQL releases the lock when the surrounding
    transaction commits or rolls back, so the critical section must stay inside that transaction.

    An instance holds no session state and can be reused, but any single acquisition belongs to the
    one session and transaction that made it.
    """

    def __init__(self, lock_args: list[Any] | tuple[Any, ...], raise_on_failure: bool = True) -> None:
        if not isinstance(raise_on_failure, bool):
            raise PgAdvisoryLockError('Raise_on_failure argument must be a bool.')
        self.raise_on_failure = raise_on_failure

        validate(lock_args)
        self.lock_args = tuple(lock_args)

        self.lock_key = get_key_from_args(self.lock_args)

    def lock_immediate(self, session: Session) -> bool:
        """Try to acquire the lock without waiting.

        Contention either raises PgAdvisoryLockNotAcquired or returns False, according to
        raise_on_failure. No lock_timeout is involved, so the call never blocks.
        """

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
        """Acquire the lock, waiting up to the given timeout.

        A zero timeout delegates to the non-blocking path. Otherwise the wait runs inside a
        savepoint with lock_timeout applied transaction-locally, so a timeout aborts only that
        savepoint and leaves the caller's transaction usable.

        Only SQLSTATE 55P03 counts as contention: it raises PgAdvisoryLockTimeout or returns False,
        according to raise_on_failure. Every other database error propagates unchanged. The boolean
        mode discards the originating error, so use the exception mode when the cause matters,
        where it is available as __cause__.
        """

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
