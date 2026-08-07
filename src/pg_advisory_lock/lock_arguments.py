import hashlib
import json
from typing import Any

from sqlalchemy import Table
from sqlalchemy.orm import DeclarativeBase

from .exceptions import PgAdvisoryLockError


def validate(args: Any) -> None:
    if not isinstance(args, (list, tuple)):
        raise PgAdvisoryLockError('Lock arguments must be a list or tuple.')

    if not args:
        raise PgAdvisoryLockError('At least one lock argument is required.')

    for _arg in args:
        if _arg is None:
            raise PgAdvisoryLockError('Lock argument can not be "None".')


def normalize(arg: Any) -> str:
    if isinstance(arg, DeclarativeBase):  # SQL Alchemy Model
        return str(arg.__tablename__)
    elif isinstance(arg, Table):  # SQL Alchemy Table
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
