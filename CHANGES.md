# Changelog

All notable changes to PG Advisory Lock will be documented in this file.


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
