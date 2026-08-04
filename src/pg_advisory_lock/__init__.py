from importlib.metadata import version

from .exceptions import PgAdvisoryLockError, PgAdvisoryLockNotAcquired, PgAdvisoryLockTimeout
from .lock import PGAdvisoryLock

__all__ = ['PGAdvisoryLock', 'PgAdvisoryLockError', 'PgAdvisoryLockTimeout', 'PgAdvisoryLockNotAcquired']

__version__ = version('pg-advisory-lock')
