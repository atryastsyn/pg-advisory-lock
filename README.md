# pg-advisory-lock

## Pythonic PostgreSQL advisory locking for SQLAlchemy, with flexible keys and pluggable failure handling.

Provides a high-level interface for acquiring PostgreSQL advisory locks with flexible
parameter handling and timeout support. Advisory locks are application-level locks
that are automatically released when the transaction ends.


### Key features:
- Flexible lock key generation from various argument types (models, tables, strings, etc.)
- Non-blocking immediate lock acquisition
- Blocking lock acquisition with configurable timeout
- Automatic lock release on transaction end (uses pg_advisory_xact_lock functions)
- Configurable failure handling: raise exceptions (default) or return boolean
- Robust exception handling that treats any failure as "lock not acquired"


### Failure handling modes:
- raise_on_failure=True (default): Raises PgAdvisoryLockTimeout on any lock acquisition failure
- raise_on_failure=False: Returns False on failure, allowing graceful handling of lock contention


### Usage examples:
#### Default behavior: raises exception on failure (safe by default):

```
locker = PGAdvisoryLock(db_session, [UserModel, user_id])
locker.lock()  # Raises PgAdvisoryLockTimeout if lock cannot be acquired
# Proceed knowing lock is held
```


#### Boolean mode: explicit handling of lock contention:

```
locker = PGAdvisoryLock(db_session, [UserModel, user_id], raise_on_failure=False)
if locker.lock(timeout_in_ms=5000):
    # Got lock, proceed with critical section
    process_payment()
else:
    # Handle lock contention gracefully
    schedule_retry()
```


#### Immediate (non-blocking) attempts:

```
locker = PGAdvisoryLock(db_session, ["payment_processing", order_id])
if locker.lock_immediate():  # Raises by default
    # Got lock immediately
    pass
```


#### Lock on multiple components:

```
locker = PGAdvisoryLock(db_session, ["user_sync", region, user_id])
if locker.lock():  # Default 1 second timeout, raises on failure
    # Process user sync
    pass
```


### Lock key generation:
- SQLAlchemy models/tables → table name
- Other objects → string representation
- All components joined with ":" and hashed to 64-bit signed integer


### Thread safety
- Each instance should be used within a single database session/transaction.
