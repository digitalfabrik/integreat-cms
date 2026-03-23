"""
Shared configuration for status code tests.

These parametrized view tests run every view x every role combination,
producing thousands of test cases. Mark the entire directory as slow so
developers can skip them with ``-m "not slow"`` during local iteration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add the ``slow`` marker to every test in this directory."""
    slow = pytest.mark.slow
    for item in items:
        if Path(item.fspath).parent == _THIS_DIR:
            item.add_marker(slow)
