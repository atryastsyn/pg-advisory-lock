# Changelog

## [0.0.7] - 2026-08-05

### Added

- Add strict runtime validation for the `raise_on_failure` argument.
- Add a helper for reading the current value of a PostgreSQL local setting.
- Add regression coverage for preserving transaction-local PostgreSQL settings.
- Add validation coverage for supported and unsupported lock arguments.

### Changed

- Preserve the caller's previous `lock_timeout` value after lock acquisition.
- Restore transaction-local settings to their initial values instead of PostgreSQL defaults.
- Rename the public `PGAdvisoryLock` class to `PgAdvisoryLock` for consistent Python naming.
- Centralize lock-argument container validation in the validation helper.
- Update documentation with boolean validation and `lock_timeout` restoration behavior.
- Update the project priority list.

### Notes

- Non-boolean `raise_on_failure` values now raise `PgAdvisoryLockError`.
- `lock()` temporarily changes `lock_timeout` without permanently replacing the caller's existing transaction-local value.
- The `PgAdvisoryLock` rename changes the public import name from the previous development versions.

---

## [0.0.6] - 2026-08-04

### Added

- Add regression coverage for ambiguous lock-argument boundaries.
- Add a fixed key vector to detect unintended serialization changes.
- Add coverage for intentionally type-insensitive normalization.

### Changed

- Serialize normalized lock arguments as a compact JSON array instead of joining them with `:`.
- Preserve component boundaries when lock values contain separator characters.
- Use explicit SQLAlchemy type checks when normalizing model instances and tables.
- Update key-generation documentation to describe JSON serialization and normalized-value semantics.

### Notes

- The new serialization format changes generated lock keys compared with previous versions.
- Values with the same normalized string representation, such as `1` and `'1'`, intentionally share a lock key.
- PostgreSQL’s signed 64-bit key space retains a theoretical hash-collision risk.

---

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
