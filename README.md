# pg-advisory-lock

## Pythonic PostgreSQL advisory locking for SQLAlchemy, with structured keys and explicit contention handling.

Provides a high-level interface for acquiring PostgreSQL advisory locks with structured
lock arguments and timeout support. Advisory locks are application-level locks that are
automatically released when the transaction commits or rolls back.

### Install
```bash
pip install pg-advisory-lock
```

Requires Python 3.12+ and SQLAlchemy 2.x.


### Key features:
- Deterministic lock keys composed from `str`, `int`, and `uuid.UUID` components
- Non-blocking immediate lock acquisition
- Blocking lock acquisition with configurable timeout
- Automatic lock release on transaction end (uses pg_advisory_xact_lock functions)
- Configurable handling for expected lock contention: raise exceptions (default) or return a boolean
- Database and infrastructure errors are propagated unchanged
- Inline type hints shipped with the package (PEP 561)


### Failure handling
`raise_on_failure` controls expected lock contention only:

- `raise_on_failure=True` (default):
  - `lock_immediate()` raises `PgAdvisoryLockNotAcquired` when the lock is already held.
  - `lock()` raises `PgAdvisoryLockTimeout` when its timeout expires.
- `raise_on_failure=False`:
  - Both methods return `False` for expected contention or timeout.
- Unexpected database and infrastructure errors are always propagated.

`raise_on_failure` must be a boolean. Other values raise `PgAdvisoryLockError`.

`PgAdvisoryLockTimeout` is a subclass of `PgAdvisoryLockNotAcquired`.

Boolean mode discards the originating database error. Use the default exception mode when the
cause matters: the underlying `DBAPIError` is chained as `__cause__`.


### Usage examples:
Import the public API from the installed package:

```python
from pg_advisory_lock import (
    PgAdvisoryLock,
    PgAdvisoryLockError,
    PgAdvisoryLockNotAcquired,
    PgAdvisoryLockTimeout,
)
```

#### Default behavior: raises exception on failure (safe by default):

```python
locker = PgAdvisoryLock(lock_args=[UserModel.__table__.name, user_id])

with session.begin():
    locker.lock(session=session)
    process_payment()
```


#### Boolean mode: explicit handling of lock contention:

```python
locker = PgAdvisoryLock(lock_args=[UserModel.__table__.name, user_id], raise_on_failure=False)

with session.begin():
    if locker.lock(session=session, timeout_in_ms=5000):
        process_payment()
    else:
        schedule_retry()
```


#### Immediate (non-blocking) attempts:

```python
locker = PgAdvisoryLock(
    lock_args=['payment_processing', order_id],
    raise_on_failure=False,
)

with session.begin():
    if locker.lock_immediate(session=session):
        process_payment()
    else:
        schedule_retry()
```


#### Lock on multiple components:

```python
locker = PgAdvisoryLock(lock_args=['user_sync', region, user_id])

with session.begin():
    locker.lock(session=session)
    synchronize_user()
```

### Transaction behavior
The library uses transaction-scoped advisory locks. The critical section must remain
inside the same open transaction in which the lock was acquired. Committing or rolling
back that transaction releases the lock automatically.

When `lock()` reaches its timeout, the failed PostgreSQL statement is isolated within
a savepoint. After `False` is returned or `PgAdvisoryLockTimeout` is caught, the caller's
outer transaction remains usable.

`lock()` temporarily changes the transaction-local PostgreSQL `lock_timeout`. After a
successful acquisition or handled timeout, the caller's previous `lock_timeout` value
is restored.

A connection or infrastructure failure cannot be repaired by a savepoint and is
propagated to the caller.

### PostgreSQL advisory lock caveats
PostgreSQL advisory locks have a few well-known caveats. This library inherits them; it does not
remove or wrap them away. You should account for them when taking more than one lock or holding
many distinct keys in one transaction.

Details are in the [PostgreSQL advisory-lock documentation](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS).

- Taking more than one advisory lock in a transaction can deadlock if another session takes the
  same locks in the opposite order. Use a consistent application order (for example parent before
  child, or a stable resource identity). Do not sort by `lock_key`.
- `lock()` sets a transaction-local `lock_timeout` (default 1000 ms). PostgreSQL's deadlock detector
  only runs after `deadlock_timeout` (also 1 s by default). When `lock_timeout` expires first, a
  real deadlock is reported as SQLSTATE `55P03` and becomes `PgAdvisoryLockTimeout` or `False`,
  same as ordinary contention. A longer `timeout_in_ms` can instead surface `40P01`, which this
  library does not treat as contention.
- Each distinct advisory lock occupies a slot in PostgreSQL's shared lock table, sized from
  `max_locks_per_transaction` and shared with ordinary relation and row locks. Exhaustion is an
  out-of-shared-memory error, not `55P03`, and is propagated unchanged.

### Lock arguments and key generation
`lock_args` must be a non-empty list or tuple. A bare string, set, mapping, generator,
or other iterable is rejected.

The arguments are copied to an immutable tuple during construction, so later changes
to the original list do not affect the lock identity.

For a lock with one component, wrap the value in a list or one-element tuple:

```python
PgAdvisoryLock(lock_args=['payment_processing'])
PgAdvisoryLock(lock_args=('payment_processing',))
```

Each component must be a `str`, `int`, or `uuid.UUID`. Any other type, including `None`, SQLAlchemy
model instances, model classes, and `Table` objects, raises `PgAdvisoryLockError` at construction.

The restriction exists because a value relying on Python's default `repr` stringifies with a memory
address that differs in every process. Hashing one would derive a key that never matches another
process, so the lock would appear granted while excluding nobody.

Pass the table name explicitly:

```python
locker = PgAdvisoryLock(lock_args=[UserModel.__table__.name, user.id])
```

`__table__.name` avoids duplicating the table name in application code. Note that renaming the table
changes the derived key, whereas a string literal would not.

The normalized strings are serialized as a compact JSON array, preserving component
boundaries even when values contain separators. The serialized value is hashed with
SHA-256 and mapped to PostgreSQL's signed 64-bit advisory-lock key range.

Normalization is intentionally type-insensitive, so values with the same normalized
string representation, such as `1` and `'1'`, produce the same lock key.


### Thread safety
- An instance keeps no state after construction and can be shared across sessions and threads.
- Each thread needs its own `Session`; SQLAlchemy sessions are not thread-safe.
- A single acquisition belongs to the session and transaction that made it.


## Development

### Running tests
Install the project and its development dependencies:

```bash
poetry install
```

Start the local PostgreSQL test database and run the test suite:

```bash
docker compose up -d
poetry run pytest
```

Tests connect to the following database by default:

```text
postgresql+psycopg://postgres:123@localhost:6543/testing
```

Override the database URL when using another PostgreSQL instance:

```bash
TEST_DATABASE_URL='postgresql+psycopg://user:password@host:5432/database' \
  poetry run pytest
```

Stop the local test database when it is no longer needed:

```bash
docker compose down
```

### Checks and GitHub workflows

Run the same checks locally as the [CI workflow](.github/workflows/ci.yaml):

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy
poetry run pytest
poetry build
```

CI runs on pull requests targeting `master` and pushes to `master`. It runs linting,
formatting, type checks, tests against PostgreSQL, and a package build.

### Releasing to PyPI

1. Update the version in `pyproject.toml` and add the release notes to `CHANGES.md`.
   Merge these changes into `master` and wait for CI to pass.
2. Switch to the latest `master` and confirm the package version:

   ```bash
   git switch master
   git pull --ff-only origin master
   poetry version -s
   ```

3. Create an annotated tag matching that version, then push the tag. For version
   `0.1.3`:

   ```bash
   git tag -a v0.1.3 -m "Release v0.1.3"
   git push origin v0.1.3
   ```

Pushing a `v*` tag starts the [Release workflow](.github/workflows/release.yaml).
It builds the distributions from the tagged commit and publishes them to PyPI using
trusted publishing through the `pypi` GitHub environment. The release workflow
does not run the CI checks, so tag the commit that passed CI. The package version
comes from `pyproject.toml`; creating a tag does not update it.

### VS Code tasks

Use **Tasks: Run Task** to run the tasks in [.vscode/tasks.json](.vscode/tasks.json).
The release flow uses `go-to-master`, `project-version`, `git-create-tag`, and
`git-push-tag`, in that order. Both tag tasks prompt for the release version without
the `v` prefix; enter the same version shown by `project-version` for each task.

Tasks also cover dependency installation, formatting, type checks, tests, and the
local PostgreSQL service. The `docker-down` task removes the database volume as well
as stopping the service.


## License

MIT. See [LICENSE](LICENSE).
