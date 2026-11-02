from __future__ import annotations

import pytest

from .analysis import analyze_test, merge_results, normalize_sql, SQL_LENGTH
from .capture import QueryRecord

pytestmark = pytest.mark.unit


def _query(
    sql: str = "SELECT * FROM cms_region WHERE id = %s",
    params: str = "(1,)",
    duration: float = 0.001,
    call_site: str = "integreat_cms/cms/views/a.py:10 in view",
    route: str | None = None,
    request_id: int | None = None,
) -> QueryRecord:
    return QueryRecord(
        sql=sql,
        params=params,
        duration=duration,
        many=False,
        alias="default",
        route=route,
        request_id=request_id,
        call_site=call_site,
        stack=[call_site],
    )


def test_normalize_collapses_in_lists() -> None:
    assert (
        normalize_sql("SELECT  *\n FROM t WHERE id IN (%s, %s, %s) AND x = %s")
        == "SELECT * FROM t WHERE id IN (...) AND x = %s"
    )


def test_normalize_collapses_savepoint_names() -> None:
    assert (
        normalize_sql('SAVEPOINT "s281472923212704_x896"') == 'SAVEPOINT "<savepoint>"'
    )
    assert (
        normalize_sql('RELEASE SAVEPOINT "s1_x2"') == 'RELEASE SAVEPOINT "<savepoint>"'
    )


def test_duplicates_require_same_params() -> None:
    result = analyze_test(
        "tests/a.py::test",
        {"call": [_query(params="(1,)"), _query(params="(1,)"), _query(params="(2,)")]},
    )
    assert len(result["duplicates"]) == 1
    assert result["duplicates"][0]["count"] == 2
    assert result["duplicates"][0]["params"] == "(1,)"


def test_n1_requires_threshold_and_same_call_site() -> None:
    five = [_query(params=f"({i},)") for i in range(5)]
    four = [_query(params=f"({i},)") for i in range(4)]
    split = [_query(params=f"({i},)") for i in range(3)] + [
        _query(params=f"({i},)", call_site="integreat_cms/other.py:1 in f")
        for i in range(2)
    ]
    assert len(analyze_test("t::a", {"call": five})["n1"]) == 1
    assert analyze_test("t::a", {"call": five})["n1"][0]["count"] == 5
    assert analyze_test("t::b", {"call": four})["n1"] == []
    assert analyze_test("t::c", {"call": split})["n1"] == []


def test_ranking_uses_call_phase_only() -> None:
    big_setup = analyze_test(
        "tests/a.py::big_setup",
        {"setup": [_query()] * 100, "call": [_query()]},
    )
    big_call = analyze_test(
        "tests/a.py::big_call",
        {"setup": [_query()], "call": [_query()] * 10},
    )
    assert big_setup["phases"] == {"setup": 100, "call": 1, "teardown": 0}

    report = merge_results([big_setup, big_call], {})
    assert [test["nodeid"] for test in report["tests"]] == [
        "tests/a.py::big_call",
        "tests/a.py::big_setup",
    ]
    assert report["totals"]["queries"] == 11
    assert report["totals"]["setup_queries"] == 101


def test_merge_aggregates_endpoints_across_tests() -> None:
    first = analyze_test(
        "tests/a.py::one",
        {"call": [_query(route="api/v3/regions/", request_id=1)] * 3},
    )
    second = analyze_test(
        "tests/b.py::two",
        {
            "call": [_query(route="api/v3/regions/", request_id=2)] * 5
            + [_query(route=None)]
        },
    )
    report = merge_results([first, second], {})
    assert report["endpoints"] == [
        {
            "route": "api/v3/regions/",
            "tests": 2,
            "requests": 2,
            "queries": 8,
            "max_per_request": 5,
        }
    ]


def test_empty_inputs() -> None:
    report = merge_results([], {"workers": 0})
    assert report["meta"] == {"workers": 0}
    assert report["totals"]["tests"] == 0
    assert report["totals"]["queries"] == 0
    assert report["tests"] == []
    assert report["endpoints"] == []

    empty = analyze_test("t::empty", {})
    assert empty["total"] == 0
    assert empty["phases"] == {"setup": 0, "call": 0, "teardown": 0}


def test_report_stays_compact() -> None:
    long_sql = "x" * 2 * SQL_LENGTH
    result = analyze_test("t::long", {"call": [_query(sql=long_sql)] * 2})
    assert len(result["slowest"][0]["sql"]) == SQL_LENGTH
    assert len(result["duplicates"][0]["sql"]) == SQL_LENGTH

    report = merge_results([result], {})
    assert "shapes" not in report["tests"][0]
    assert report["shapes"][0]["count"] == 2
