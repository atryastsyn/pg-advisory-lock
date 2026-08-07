"""Public exception hierarchy and classification of PostgreSQL lock-contention errors."""

from sqlalchemy.exc import DBAPIError


class PgAdvisoryLockError(Exception):
    """Base error for every failure raised by this library.

    Also covers misuse detected before any database call, such as an invalid lock-argument
    container or a non-boolean raise_on_failure.
    """


class PgAdvisoryLockNotAcquired(PgAdvisoryLockError):
    """Raised when the lock is already held and immediate acquisition cannot proceed."""


class PgAdvisoryLockTimeout(PgAdvisoryLockNotAcquired):
    """Raised when a blocking acquisition exceeds its timeout.

    Subclasses PgAdvisoryLockNotAcquired so a single except clause catches every contention outcome.
    """


LOCK_NOT_AVAILABLE_CODE = '55P03'


def lock_is_not_available(error: DBAPIError) -> bool:
    """Report whether a database error is lock contention rather than a real failure.

    Only SQLSTATE 55P03 counts as contention. Psycopg 3 exposes it as sqlstate and Psycopg 2 as
    pgcode, so both are probed with sqlstate taking precedence. Anything else, including a driver
    that exposes neither attribute, is treated as unrelated so the caller propagates it.
    """

    if hasattr(error.orig, 'sqlstate'):
        return bool(getattr(error.orig, 'sqlstate', None) == LOCK_NOT_AVAILABLE_CODE)
    elif hasattr(error.orig, 'pgcode'):
        return bool(getattr(error.orig, 'pgcode', None) == LOCK_NOT_AVAILABLE_CODE)
    else:
        return False
