from importlib import reload
from importlib.metadata import PackageNotFoundError, version
from unittest.mock import patch

import pg_advisory_lock


def test_version_uses_package_metadata():
    assert pg_advisory_lock.__version__ == version('pg-advisory-lock')


def test_version_fallback_to_default_value():
    with patch('importlib.metadata.version', side_effect=PackageNotFoundError):
        reload(pg_advisory_lock)
        assert pg_advisory_lock.__version__ == '0.0.0+unknown'
    reload(pg_advisory_lock)
