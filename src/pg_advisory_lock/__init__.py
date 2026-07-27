from importlib.metadata import version

from .exceptions import PgAdvisoryLockError, PgAdvisoryLockTimeout
from .lock import PGAdvisoryLock

__all__ = ['PGAdvisoryLock', 'PgAdvisoryLockError', 'PgAdvisoryLockTimeout']

__version__ = version('pg-advisory-lock')
