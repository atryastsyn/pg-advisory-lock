import hashlib
from typing import Any

from .exceptions import PgAdvisoryLockError


def validate(args: tuple[Any, ...]):
    if not args:
        raise PgAdvisoryLockError('At least one lock argument is required.')

    for _arg in args:
        if _arg is None:
            raise PgAdvisoryLockError('Lock argument can not be "None".')


def normalize(arg: Any) -> str:
    if hasattr(arg, '__tablename__'):  # SQL Alchemy Model
        return arg.__tablename__
    elif hasattr(arg, 'name'):  # SQL Alechemy Table
        return arg.name
    else:
        return str(arg)


def get_key_from_args(args: tuple[Any, ...]) -> int:
    """Compute a 64-bit signed integer key for PostgreSQL advisory locks from lock arguments.

    This method converts variable lock arguments into a deterministic 64-bit key by:
    1. Normalizing each argument to a string representation
    2. Joining them with ':' delimiter
    3. Hashing with SHA-256 and taking first 8 bytes as 64-bit integer
    4. Converting to PostgreSQL's signed 64-bit range

    Hash collision probability is acceptable because:
    - SHA-256 provides strong collision resistance with uniform distribution
    - 64-bit key space (2^64 ≈ 18 quintillion values) is vast relative to typical usage
    - Birthday paradox suggests ~50% collision chance only after ~4 billion distinct lock keys
    - Most applications use far fewer than millions of different lock combinations
    - Collision consequences are performance degradation (false lock contention), not correctness issues
    - PostgreSQL advisory locks natively use 64-bit integers, so this matches the available space

    Even in the unlikely event of a collision, two logically different locks would simply
    serialize unnecessarily, which is safe but suboptimal - much better than the alternative
    of complex collision handling that could introduce deadlocks or other concurrency bugs.

    Returns:
        64-bit signed integer suitable for pg_advisory_xact_lock()
    """

    parts = [normalize(_arg) for _arg in args]
    joined = ':'.join(parts)
    digest = hashlib.sha256(joined.encode('utf-8')).digest()
    raw = int.from_bytes(digest[:8], 'big')
    return raw - (1 << 64) if raw & (1 << 63) else raw
