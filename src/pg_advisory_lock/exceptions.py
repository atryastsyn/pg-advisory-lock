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
        return error.orig.sqlstate == LOCK_NOT_AVAILABLE_CODE  # type: ignore
    elif hasattr(error.orig, 'pgcode'):
        return error.orig.pgcode == LOCK_NOT_AVAILABLE_CODE   # type: ignore
    else:
        return False
