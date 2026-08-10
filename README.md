# pg-advisory-lock

## Pythonic PostgreSQL advisory locking for SQLAlchemy, with structured keys and explicit contention handling.

Provides a high-level interface for acquiring PostgreSQL advisory locks with structured
lock arguments and timeout support. Advisory locks are application-level locks that are
automatically released when the transaction commits or rolls back.


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
docker compose -f docker/compose.yaml up -d
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
docker compose -f docker/compose.yaml down
```


## License

MIT. See [LICENSE](LICENSE).
