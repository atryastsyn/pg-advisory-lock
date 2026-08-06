import pytest
from sqlalchemy.exc import OperationalError

from pg_advisory_lock.exceptions import lock_is_not_available


class FakeOrig:
    def __init__(self, *, sqlstate: str | None = None, pgcode: str | None = None):
        if sqlstate is not None:
            self.sqlstate = sqlstate
        if pgcode is not None:
            self.pgcode = pgcode


@pytest.mark.parametrize(
    argnames='orig_kwargs,expected',
    argvalues=(
        ({'sqlstate': '55P03'}, True),
        ({'pgcode': '55P03'}, True),
        ({'sqlstate': '55P03', 'pgcode': '55P03'}, True),
        ({'sqlstate': '57014'}, False),  # Query Cancelled
        ({'pgcode': '57014'}, False),
        ({'sqlstate': '40P01'}, False),  # Deadlock
        ({'sqlstate': '08006'}, False),  # Connection Failure
        ({'sqlstate': '22023'}, False),  # Invalid parameter
        ({}, False),
        ({'sqlstate': '40P01', 'pgcode': '55P03'}, False),  # sqlstate wins
    ),
)
def test_lock_is_not_available_condition_expected(orig_kwargs, expected):
    orig = FakeOrig(**orig_kwargs)
    error = OperationalError(statement='SELECT 1;', params={}, orig=orig)  # type: ignore
    assert lock_is_not_available(error=error) is expected
