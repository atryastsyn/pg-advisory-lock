# TODO

## Next

- [ ] Make lock-key serialization unambiguous and type-aware.
- [ ] Validate that raise_on_failure is strictly a bool.
- [ ] Preserve the caller’s previous lock_timeout.
- [ ] Add rollback-release, re-entrancy, and broader SQLSTATE tests.
- [ ] Fix test database configuration and timing flakiness.
- [ ] Import the installed package instead of src.pg_advisory_lock.
- [ ] Fix Ruff source globs and add CI.
- [ ] Complete typing, docstrings, logging, and package metadata.

## Backlog

- [ ] Docs

## Ideas

- [ ] Get the `statement_timeout` and make sure `lock_timeout` is less or equal
- [ ] Do I need `psycopg` be package dependency or just DEV?
