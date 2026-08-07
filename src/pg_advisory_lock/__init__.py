"""Transaction-scoped PostgreSQL advisory locks for SQLAlchemy sessions."""

from importlib.metadata import version

from .exceptions import PgAdvisoryLockError, PgAdvisoryLockNotAcquired, PgAdvisoryLockTimeout
from .lock import PgAdvisoryLock

__all__ = ['PgAdvisoryLock', 'PgAdvisoryLockError', 'PgAdvisoryLockTimeout', 'PgAdvisoryLockNotAcquired']

__version__ = version('pg-advisory-lock')
