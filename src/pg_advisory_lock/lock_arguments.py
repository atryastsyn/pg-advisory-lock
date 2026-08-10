"""Validation and deterministic key derivation for advisory-lock arguments."""

import hashlib
import json
import uuid
from typing import Any

from .exceptions import PgAdvisoryLockError

LOCK_ARGUMENT_TYPES: tuple[type, ...] = (str, int, uuid.UUID)
LOCK_ARGUMENT_TYPE_NAMES = ', '.join([_.__name__ for _ in LOCK_ARGUMENT_TYPES])


def validate(args: Any) -> None:
    """Enforce the lock-argument contract before a key is derived.

    Only lists and tuples are accepted. Bare strings, sets, mappings, and generators are rejected
    because they iterate per character, have no stable order, or would be consumed on first use.
    None is rejected because it cannot be told apart from the string 'None'.

    Components are restricted to str, int, and UUID, whose str() is stable across processes. Anything
    else, including ORM instances, model classes, and Table objects, is rejected rather than hashed: a
    value relying on the default repr embeds a memory address and would derive a different key in every
    process, granting a lock that excludes nobody.
    """

    if not isinstance(args, (list, tuple)):
        raise PgAdvisoryLockError('Lock arguments must be a list or tuple.')

    if not args:
        raise PgAdvisoryLockError('At least one lock argument is required.')

    for _arg in args:
        if _arg is None:
            raise PgAdvisoryLockError('Lock argument can not be "None".')
        if not isinstance(_arg, LOCK_ARGUMENT_TYPES):
            raise PgAdvisoryLockError(
                f'Lock argument must be one of "{LOCK_ARGUMENT_TYPE_NAMES}", got "{type(_arg).__name__}" instead.'
            )


def normalize(arg: Any) -> str:
    """Reduce one lock component to the string used for key derivation.

    Normalization is deliberately type-insensitive: 1 and '1' yield the same component, so an integer
    primary key and its string form address the same lock.
    """

    return str(arg)


def get_key_from_args(args: tuple[Any, ...]) -> int:
    """Build a deterministic signed 64-bit PostgreSQL advisory-lock key.

    Components are normalized to strings and serialized as a compact JSON array so
    component boundaries remain unambiguous. The first eight bytes of the SHA-256
    digest are mapped to PostgreSQL's signed bigint range.

    Truncating the digest retains a theoretical 64-bit hash-collision risk. A collision
    only causes unrelated operations to serialize on the same advisory lock.
    """

    serialized = json.dumps(obj=[normalize(_arg) for _arg in args], ensure_ascii=False, separators=(',', ':'))
    digest = hashlib.sha256(serialized.encode('utf-8')).digest()
    raw = int.from_bytes(digest[:8], 'big')
    return raw - (1 << 64) if raw & (1 << 63) else raw
