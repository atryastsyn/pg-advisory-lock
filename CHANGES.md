# Changelog

All notable changes to PG Advisory Lock will be documented in this file.



## [0.0.5] - 2026-08-04

### Added

- Add `PgAdvisoryLockNotAcquired` for immediate lock contention.
- Add regression tests proving the outer transaction remains usable after a lock timeout.
- Add tests for database-error propagation and PostgreSQL lock-timeout classification.
- Add validation tests for supported and unsupported `lock_args` containers.

### Changed

- Isolate blocking lock acquisition within a savepoint so PostgreSQL lock timeouts do not abort the caller's transaction.
- Treat only PostgreSQL SQLSTATE `55P03` as expected lock contention; propagate database and infrastructure errors.
- Support SQLSTATE detection for both Psycopg 3 (`sqlstate`) and Psycopg 2 (`pgcode`).
- Make `PgAdvisoryLockTimeout` a subclass of `PgAdvisoryLockNotAcquired`.
- Restrict `lock_args` to non-empty lists and tuples and store them as an immutable tuple.
- Simplify local `lock_timeout` cleanup around savepoint rollback.
- Update documentation with transaction boundaries, failure semantics, and the `lock_args` contract.
- Fix Ruff source-file discovery for the package directory.
- Align the Docker PostgreSQL container name and healthcheck with the test service configuration.

### Notes

- Lock contention can still raise exceptions or return `False`, according to `raise_on_failure`.
- Unexpected database and infrastructure errors are always propagated to the caller.


---

## [0.0.4] - 2026-08-04

### Added

- Add `psycopg` as DEV dependency.
- Add test PG instance with Docker Container.
- Add tests for `lock.py` methods with real SQL Alchemy Session.

### Changed

- TODO updated.

### Notes

---

## [0.0.3] - 2026-07-28

### Added

- Add tests for `lock_argumets.py` methods
- Add test drafts for `lock.py` methods
- Add facade method to update a `lock_timeout` local setting

### Changed

- TODO updated

### Notes

---

## [0.0.2] - 2026-07-28

### Added

- Add a new `PGAdvisoryLock` class to be imported by third-party code.
- Add new exception classes - `PgAdvisoryLockError` and `PgAdvisoryLockTimeout` to be imported by third-party code.
- Add new service file - `lock_arguments.py` - to deal with lock arguments
- Add new service file - `pg_lock_settings.py` - to deal with local settings in the current DB Session

### Changed

- TODO updated

### Notes

- A class prototype is in place. Now it is time to cover its functionality with tests.

---

## [0.0.1] - 2026-07-27

### Added

### Changed

### Notes

- The package `pg-advisory-lock` is all-set now. Ready to evolve
