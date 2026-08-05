# TODO

## Next

- [ ] Import the installed package instead of src.pg_advisory_lock.
- [ ] Fix test database configuration and timing flakiness.
- [ ] Add rollback-release, re-entrancy, and broader SQLSTATE tests.
- [ ] Fix Ruff source globs and add CI.
- [ ] Complete typing, docstrings, logging, and package metadata.

## Backlog

- [ ] Docs

## Ideas

- [ ] Get the `statement_timeout` and make sure `lock_timeout` is less or equal
- [ ] Do I need `psycopg` be package dependency or just DEV?
