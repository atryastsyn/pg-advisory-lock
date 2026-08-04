# pg-advisory-lock

## Pythonic PostgreSQL advisory locking for SQLAlchemy, with flexible keys and explicit contention handling.

Provides a high-level interface for acquiring PostgreSQL advisory locks with structured
lock arguments and timeout support. Advisory locks are application-level locks that are
automatically released when the transaction commits or rolls back.


### Key features:
- Flexible lock key generation from various argument types (models, tables, strings, etc.)
- Non-blocking immediate lock acquisition
- Blocking lock acquisition with configurable timeout
- Automatic lock release on transaction end (uses pg_advisory_xact_lock functions)
- Configurable handling for expected lock contention: raise exceptions (default) or return a boolean
- Database and infrastructure errors are propagated unchanged


### Failure handling
`raise_on_failure` controls expected lock contention only:

- `raise_on_failure=True` (default):
  - `lock_immediate()` raises `PgAdvisoryLockNotAcquired` when the lock is already held.
  - `lock()` raises `PgAdvisoryLockTimeout` when its timeout expires.
- `raise_on_failure=False`:
  - Both methods return `False` for expected contention or timeout.
- Unexpected database and infrastructure errors are always propagated.

`PgAdvisoryLockTimeout` is a subclass of `PgAdvisoryLockNotAcquired`.


### Usage examples:
#### Default behavior: raises exception on failure (safe by default):

```python
locker = PGAdvisoryLock(lock_args=[UserModel, user_id])

with session.begin():
    locker.lock(session=session)
    process_payment()
```


#### Boolean mode: explicit handling of lock contention:

```python
locker = PGAdvisoryLock(lock_args=[UserModel, user_id], raise_on_failure=False)

with session.begin():
    if locker.lock(session=session, timeout_in_ms=5000):
        process_payment()
    else:
        schedule_retry()
```


#### Immediate (non-blocking) attempts:

```python
locker = PGAdvisoryLock(
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
locker = PGAdvisoryLock(lock_args=['user_sync', region, user_id])

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

A connection or infrastructure failure cannot be repaired by a savepoint and is
propagated to the caller.

### Lock arguments and key generation
`lock_args` must be a non-empty list or tuple. A bare string, set, mapping, generator,
or other iterable is rejected. Each component must be non-`None`.

The arguments are copied to an immutable tuple during construction, so later changes
to the original list do not affect the lock identity.

For a lock with one component, wrap the value in a list or one-element tuple:

```python
PGAdvisoryLock(lock_args=['payment_processing'])
PGAdvisoryLock(lock_args=('payment_processing',))
```

Lock components are normalized as follows:

- SQLAlchemy models and tables → table name
- Other supported objects → string representation
- All components are joined with `:` and hashed to a signed 64-bit integer


### Thread safety
- Each instance should be used within a single database session and transaction.
