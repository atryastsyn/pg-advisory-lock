# Changelog

All notable changes to PG Advisory Lock are documented in this file.

## [0.0.16] - 2026-09-16

### Changed

- Deploy flow to publish the project to PyPi.

## [0.0.15] - 2026-09-08

### Added

- Add `pytest-cov` as a development dependency.
- Measure `src` coverage on every `pytest` run and fail below 90%.

### Changed

- Update the package version and project priority list.

### Notes

- Coverage is now part of the CI contract: the existing `pytest` step fails when the threshold is missed.

## [0.0.14] - 2026-08-10

### Changed

- Restrict lock components to `str`, `int`, and `UUID`; any other type is rejected at construction.
- Reduce `normalize` to a plain string conversion, so key derivation no longer imports SQLAlchemy.
- Update the package version, project priority list, and the key wording in the README and package
  description.

### Removed

- Remove the table-name normalization of `DeclarativeBase` instances and `Table` objects.

### Notes

- Breaking change: `lock_args` holding a model instance or a `Table` now raises `PgAdvisoryLockError` at
  construction instead of deriving a key. A value relying on the default `repr` embedded a memory address
  and derived a different key in every process, granting a lock that excluded nobody.
- The migration preserves keys: `[UserModel.__table__.name, user.id]` derives what `[user, user.id]` did,
  so old and new processes keep excluding each other during a rolling deploy.

---

## [0.0.13] - 2026-08-07

### Added

- Add an MIT `LICENSE`, shipped inside the built distributions.
- Add package metadata: license, keywords, and classifiers.
- Document every module, class, and public function with docstrings.

### Changed

- Document that only `DeclarativeBase` instances and `Table` objects normalize to a table name, and pass
  `Model.__table__` in the README examples.
- Clarify the README thread-safety guarantee and note the chained `__cause__` in boolean mode.
- Update the package version and project priority list.

### Notes

- Recognizing model classes in `normalize` stays open and is tracked in `TODO.md`.

---

## [0.0.12] - 2026-08-07

### Added

- Add a `py.typed` marker so type checkers honor the package's inline annotations.
- Add strict mypy checking for the package source and a CI type-check step.

### Changed

- Complete missing return annotations, including the transaction-local setting context managers.
- Replace type suppressions in SQLSTATE classification with defensive attribute lookups.
- Update the package version and project priority list.

### Notes

- Published annotations are now part of the public contract and are enforced on every push.

---

## [0.0.11] - 2026-08-06

### Added

- Add Gitea Actions CI for linting, formatting, PostgreSQL-backed tests, and package builds.

### Changed

- Expand Ruff test discovery to include nested test directories.
- Update the package version and project priority list.

### Notes

- CI runs for pushes and pull requests using a health-checked PostgreSQL service.

---

## [0.0.10] - 2026-08-06

### Added

- Add regression tests for re-entrant acquisition and lock release after rollback.
- Add SQLSTATE classification coverage for contention and unrelated database errors.

### Changed

- Update the package version and project priority list.

### Notes

- This release expands test coverage without changing runtime behavior.

---

## [0.0.9] - 2026-08-05

### Added

- Add `TEST_DATABASE_URL` support and development documentation for integration tests.
- Add reusable session-scoped engine and session factory fixtures and a function-scoped session fixture.

### Changed

- Align the default test database URL with the Docker Compose configuration.
- Make concurrency tests deterministic using monotonic clocks, explicit synchronization, and
  `pg_blocking_pids()`.

### Notes

- Integration tests use the local Docker PostgreSQL service by default.

---

## [0.0.8] - 2026-08-05

### Added

- Add a README example importing the complete public API from the installed package.

### Changed

- Import `pg_advisory_lock` in tests instead of the source-tree path `src.pg_advisory_lock`.
- Update mock targets to use the installed package namespace.
- Improve local-setting restoration coverage for both `lock_timeout` and `statement_timeout`.
- Update the package version and project priority list.

### Notes

- The distribution name remains `pg-advisory-lock`, while Python code imports `pg_advisory_lock`.
- Tests now exercise the same package namespace used by library consumers.

---

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
- `lock()` temporarily changes `lock_timeout` without permanently replacing the caller's existing
  transaction-local value.
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
- PostgreSQL's signed 64-bit key space retains a theoretical hash-collision risk.

---

## [0.0.5] - 2026-08-04

### Added

- Add `PgAdvisoryLockNotAcquired` for immediate lock contention.
- Add regression tests proving the outer transaction remains usable after a lock timeout.
- Add tests for database-error propagation and PostgreSQL lock-timeout classification.
- Add validation tests for supported and unsupported `lock_args` containers.

### Changed

- Isolate blocking lock acquisition within a savepoint so PostgreSQL lock timeouts do not abort the caller's
  transaction.
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

- Add `psycopg` as a development dependency.
- Add a PostgreSQL test instance using Docker Compose.
- Add tests for `lock.py` using real SQLAlchemy sessions.

### Changed

- Update the project priority list.

### Notes

---

## [0.0.3] - 2026-07-28

### Added

- Add tests for `lock_arguments.py`.
- Add test drafts for `lock.py`.
- Add a helper for setting transaction-local `lock_timeout`.

### Changed

- Update the project priority list.

### Notes

---

## [0.0.2] - 2026-07-28

### Added

- Add the public `PGAdvisoryLock` class.
- Add the public `PgAdvisoryLockError` and `PgAdvisoryLockTimeout` exception classes.
- Add `lock_arguments.py` for lock-argument handling.
- Add `pg_local_setting.py` for transaction-local PostgreSQL settings.

### Changed

- Update the project priority list.

### Notes

- A class prototype is in place. Now it is time to cover its functionality with tests.

---

## [0.0.1] - 2026-07-27

### Added

### Changed

### Notes

- Complete the initial `pg-advisory-lock` package scaffolding.
