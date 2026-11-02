from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from .analysis import analyze_test
from .capture import QueryRecord
from .plugin import merge_raw_results, PLUGIN_NAME, QueryReportPlugin
from .render import render_html

if TYPE_CHECKING:
    from pathlib import Path


def _result(nodeid: str, sql: str = "SELECT 1") -> dict:
    record = QueryRecord(
        sql=sql,
        params="()",
        duration=0.002,
        many=False,
        alias="default",
        route="api/v3/regions/",
        request_id=1,
        call_site="integreat_cms/api/v3/regions.py:1 in regions",
        stack=[],
    )
    return dict(analyze_test(nodeid, {"call": [record, record]}))


def test_registered_only_with_flag(pytestconfig: pytest.Config) -> None:
    """
    The plugin is only active if ``--query-report`` is passed.
    """
    plugin = pytestconfig.pluginmanager.get_plugin(PLUGIN_NAME)
    assert (plugin is not None) == pytestconfig.getoption("query_report")


def test_controller_ignores_relayed_tests(
    pytestconfig: pytest.Config, tmp_path: Path
) -> None:
    """
    The xdist controller receives ``pytest_runtest_logfinish`` for tests it did not run and must not record them.
    """
    plugin = QueryReportPlugin(pytestconfig, tmp_path)
    plugin.pytest_runtest_logfinish("tests/a.py::relayed")
    assert plugin.results == []

    plugin.phases = {"setup": [], "call": [], "teardown": []}
    plugin.pytest_runtest_logfinish("tests/a.py::local")
    assert [result["nodeid"] for result in plugin.results] == ["tests/a.py::local"]


@pytest.mark.unit
def test_merge_from_raw_files(tmp_path: Path) -> None:
    """
    The results of all xdist workers are merged into one report.
    """
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "gw0.json").write_text(json.dumps([_result("tests/a.py::one")]))
    (raw / "gw1.json").write_text(json.dumps([_result("tests/b.py::two")]))
    (raw / "gw2.json").write_text(json.dumps([]))
    report = merge_raw_results(tmp_path, {"workers": 3})
    assert sorted(test["nodeid"] for test in report["tests"]) == [
        "tests/a.py::one",
        "tests/b.py::two",
    ]
    assert report["totals"]["queries"] == 4
    assert report["endpoints"][0]["tests"] == 2


@pytest.mark.unit
def test_merge_without_raw_files(tmp_path: Path) -> None:
    """
    A run without any recorded test still produces an empty report.
    """
    assert merge_raw_results(tmp_path, {})["totals"]["tests"] == 0


@pytest.mark.unit
def test_render_has_no_script(tmp_path: Path) -> None:
    """
    The HTML report is static and escapes SQL.
    """
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "main.json").write_text(
        json.dumps([_result("tests/a.py::one", sql="SELECT * FROM t WHERE a < %s")])
    )
    html = render_html(merge_raw_results(tmp_path, {}))
    assert "<script" not in html
    assert "a &lt; %s" in html
    assert "tests/a.py::one" in html
