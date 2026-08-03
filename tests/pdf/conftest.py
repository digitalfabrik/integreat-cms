"""
Shared fixtures for the PDF export tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from integreat_cms.cms.models import Region

_TEST_DATA = Path(__file__).parents[2] / "integreat_cms/cms/fixtures/test_data.json"


@pytest.fixture(autouse=True)
def deterministic_region_timestamps(load_test_data: None, db: None) -> None:
    """
    The PDF filename hash embeds ``region.last_updated`` (an ``auto_now`` field).
    Tests running earlier in the same process can bump it with writes that are
    committed outside their test transaction, which breaks the hard-coded
    expected hashes depending on how the test files are distributed across CI
    containers. Re-pin the fixture timestamps inside this test's transaction;
    ``update()`` bypasses ``auto_now`` and is rolled back together with the test.
    """
    fixture_timestamps = {
        obj["pk"]: obj["fields"]["last_updated"]
        for obj in json.loads(_TEST_DATA.read_text())
        if obj["model"] == "cms.region"
    }
    for pk, last_updated in fixture_timestamps.items():
        Region.objects.filter(pk=pk).update(last_updated=last_updated)
