from sqlalchemy.exc import DBAPIError


class PgAdvisoryLockError(Exception):
    pass


class PgAdvisoryLockNotAcquired(PgAdvisoryLockError):
    pass


class PgAdvisoryLockTimeout(PgAdvisoryLockNotAcquired):
    pass


LOCK_NOT_AVAILABLE_CODE = '55P03'


def lock_is_not_available(error: DBAPIError) -> bool:
    if hasattr(error.orig, 'sqlstate'):
        return bool(getattr(error.orig, 'sqlstate', None) == LOCK_NOT_AVAILABLE_CODE)
    elif hasattr(error.orig, 'pgcode'):
        return bool(getattr(error.orig, 'pgcode', None) == LOCK_NOT_AVAILABLE_CODE)
    else:
        return False
