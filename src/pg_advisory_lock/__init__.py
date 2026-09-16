"""Transaction-scoped PostgreSQL advisory locks for SQLAlchemy sessions."""

from importlib.metadata import PackageNotFoundError, version

from .exceptions import PgAdvisoryLockError, PgAdvisoryLockNotAcquired, PgAdvisoryLockTimeout
from .lock import PgAdvisoryLock

__all__ = ['PgAdvisoryLock', 'PgAdvisoryLockError', 'PgAdvisoryLockTimeout', 'PgAdvisoryLockNotAcquired']


try:
    __version__ = version('pg-advisory-lock')
except PackageNotFoundError:
    __version__ = '0.0.0+unknown'
