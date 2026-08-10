# TODO

## Next

- [ ] Measure coverage with `pytest-cov` and gate CI with `--cov-fail-under`.
- [ ] Test the declared support matrix in CI: Python 3.12 and 3.13 against SQLAlchemy 1.4 and 2.x, or narrow the pins.
- [ ] Document the deadlock hazard: recommend a consistent lock ordering, and note that the default
      1000 ms timeout can surface a real deadlock as ordinary 55P03 contention.
- [ ] Document that advisory locks consume `max_locks_per_transaction` shared lock slots.
- [ ] Decide the release signal: a version past `0.1.0` and the matching `Development Status` classifier.

## Backlog

- [ ] Separate unit and integration tests so `pytest` runs without a database.
- [ ] Survive missing distribution metadata in `__init__.py` instead of raising `PackageNotFoundError`.

## Ideas

- [ ] Publish to the private index from CI on tags.
