import logging
from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

from .exceptions import PgAdvisoryLockError, PgAdvisoryLockTimeout
from .lock_arguments import get_key_from_args, validate
from .pg_local_setting import set_lock_timeout


class PGAdvisoryLock:
    def __init__(self, lock_args: Iterable, raise_on_failure: bool = True):
        self.raise_on_failure = raise_on_failure
        self.lock_args = lock_args or []
        validate(self.lock_args)
        self.lock_key = get_key_from_args(self.lock_args)

    def _log_lock_failure(self, message: str, exc: Exception, **extra_context) -> None:
        """Log advisory lock acquisition failure and extract exception details safely."""
        exc_name = exc.__class__.__name__
        exc_message = str(exc)
        extra = {'lock_args': self.lock_args, 'lock_key': self.lock_key}
        extra.update(extra_context)
        logging.warning('%s: %s: %s', message, exc_name, exc_message, extra=extra)

    def _handle_failure(self) -> bool:
        if self.raise_on_failure:
            raise PgAdvisoryLockTimeout('Failed to acquire advisory lock.')
        else:
            return False

    def lock_immediate(self, session: Session) -> bool:
        try:
            result = session.execute(text('SELECT pg_try_advisory_xact_lock(:key)'), {'key': self.lock_key}).scalar()
            if result:
                return True

        except Exception as exc:
            # Advisory lock acquisition can fail for various reasons (connection issues, invalid session state,
            # transaction rollback, etc.). Since this is a non-blocking "try" operation, we treat any failure
            # as "lock not acquired" and let the caller decide how to handle it, rather than propagating
            # database-specific exceptions up the call stack.
            self._log_lock_failure('Failed to acquire advisory lock immediately.', exc)

        return self._handle_failure()

    def lock(self, session: Session, timeout_in_ms: int = 1000) -> bool:
        if not isinstance(timeout_in_ms, int) or timeout_in_ms < 0:
            raise PgAdvisoryLockError('Lock timeout must be a non-negative integer.')

        if timeout_in_ms == 0:
            return self.lock_immediate(session=session)

        try:
            with set_lock_timeout(session, f'{timeout_in_ms}ms'):
                session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': self.lock_key})
                return True

        except Exception as exc:
            # Any exception during lock acquisition means "lock not obtained".
            # This includes timeouts, connection issues, transaction rollbacks, etc.
            self._log_lock_failure(f'Failed to acquire advisory lock within timeout {timeout_in_ms} ms.', exc)

        return self._handle_failure()
