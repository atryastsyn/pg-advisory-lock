"""Validation and deterministic key derivation for advisory-lock arguments."""

import hashlib
import json
from typing import Any

from sqlalchemy import Table
from sqlalchemy.orm import DeclarativeBase

from .exceptions import PgAdvisoryLockError


def validate(args: Any) -> None:
    """Enforce the lock-argument contract before a key is derived.

    Only lists and tuples are accepted. Bare strings, sets, mappings, and generators are rejected
    because they iterate per character, have no stable order, or would be consumed on first use.
    None is rejected because it cannot be told apart from the string 'None'.
    """

    if not isinstance(args, (list, tuple)):
        raise PgAdvisoryLockError('Lock arguments must be a list or tuple.')

    if not args:
        raise PgAdvisoryLockError('At least one lock argument is required.')

    for _arg in args:
        if _arg is None:
            raise PgAdvisoryLockError('Lock argument can not be "None".')


def normalize(arg: Any) -> str:
    """Reduce one lock component to the string used for key derivation.

    DeclarativeBase instances and Table objects collapse to their table name, so both address the
    same lock. Every other value uses its string representation, which makes normalization
    deliberately type-insensitive: 1 and '1' yield the same component.

    Model classes and legacy declarative_base() models are not recognized and fall through to that
    string representation, which is not stable across processes. Pass Model.__table__ instead.
    """

    if isinstance(arg, DeclarativeBase):
        return str(arg.__tablename__)
    elif isinstance(arg, Table):
        return arg.name
    else:
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
