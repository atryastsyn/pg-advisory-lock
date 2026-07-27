class PgAdvisoryLockError(Exception):
    pass


class PgAdvisoryLockTimeout(PgAdvisoryLockError):
    pass
