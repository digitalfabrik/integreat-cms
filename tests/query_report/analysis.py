"""
Turn the recorded queries of a test into compact results and merge them into a suite-wide report
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing import Any, Final

    from .capture import QueryRecord

#: The test phases, in execution order
PHASES: Final = ("setup", "call", "teardown")
#: The default number of executions of the same statement from one call site to count as N+1 candidate
N1_THRESHOLD: Final = 5
#: The number of slowest queries kept per test
SLOW_TOP: Final = 5
#: The number of entries kept in the suite-wide rankings
REPORT_TOP: Final = 50
#: The maximum length of the SQL stored per test (statements selecting many columns get huge)
SQL_LENGTH: Final = 1000

_IN_LIST: Final = re.compile(r"IN \((?:%s, )*%s\)")
_WHITESPACE: Final = re.compile(r"\s+")
_SAVEPOINT: Final = re.compile(r'SAVEPOINT "[^"]+"')


class Duplicate(TypedDict):
    """
    The same statement with the same parameters executed more than once
    """

    sql: str
    params: str
    call_site: str
    count: int


class NPlusOne(TypedDict):
    """
    The same statement shape executed repeatedly with different parameters from one call site
    """

    sql: str
    call_site: str
    stack: list[str]
    count: int


class SlowQuery(TypedDict):
    """
    A single slow query
    """

    sql: str
    params: str
    call_site: str
    duration: float


class RouteUsage(TypedDict):
    """
    The queries executed by the requests to one URL route within a test
    """

    route: str
    requests: int
    queries: int
    max_per_request: int


class Shape(TypedDict):
    """
    How often a normalized statement was executed
    """

    count: int
    time: float


class TestResult(TypedDict):
    """
    The analyzed queries of a single test
    """

    nodeid: str
    file: str
    phases: dict[str, int]
    total: int
    time: float
    duplicates: list[Duplicate]
    n1: list[NPlusOne]
    slowest: list[SlowQuery]
    routes: list[RouteUsage]
    shapes: dict[str, Shape]


class Report(TypedDict):
    """
    The merged results of all tests
    """

    meta: dict[str, Any]
    totals: dict[str, Any]
    tests: list[dict[str, Any]]
    top_n1: list[dict[str, Any]]
    top_duplicates: list[dict[str, Any]]
    slowest: list[dict[str, Any]]
    endpoints: list[dict[str, Any]]
    files: list[dict[str, Any]]
    shapes: list[dict[str, Any]]


def normalize_sql(sql: str) -> str:
    """
    Normalize a statement so queries which only differ in the length of ``IN`` lists
    or in generated savepoint names are grouped together.

    :param sql: The SQL with parameter placeholders
    :return: The normalized SQL
    """
    sql = _IN_LIST.sub("IN (...)", _WHITESPACE.sub(" ", sql).strip())
    return _SAVEPOINT.sub('SAVEPOINT "<savepoint>"', sql)


def analyze_test(
    nodeid: str,
    phases: dict[str, list[QueryRecord]],
    n1_threshold: int = N1_THRESHOLD,
    slow_top: int = SLOW_TOP,
) -> TestResult:
    """
    Analyze the queries of a single test. Everything except the per-phase counts only considers the ``call`` phase.

    :param nodeid: The pytest node id of the test
    :param phases: The recorded queries per test phase
    :param n1_threshold: The minimum number of executions to count as N+1 candidate
    :param slow_top: The number of slowest queries to keep
    :return: The compact result
    """
    queries = phases.get("call", [])

    exact = Counter((query.sql, query.params, query.call_site) for query in queries)
    duplicates: list[Duplicate] = [
        {
            "sql": sql[:SQL_LENGTH],
            "params": params,
            "call_site": call_site,
            "count": count,
        }
        for (sql, params, call_site), count in exact.most_common()
        if count > 1
    ]

    by_site: defaultdict[tuple[str, str], list[QueryRecord]] = defaultdict(list)
    for query in queries:
        by_site[normalize_sql(query.sql), query.call_site].append(query)

    n1: list[NPlusOne] = sorted(
        (
            {
                "sql": sql[:SQL_LENGTH],
                "call_site": call_site,
                "stack": group[0].stack,
                "count": len(group),
            }
            for (sql, call_site), group in by_site.items()
            if len(group) >= n1_threshold and len({query.params for query in group}) > 1
        ),
        key=lambda candidate: -candidate["count"],
    )

    slowest: list[SlowQuery] = [
        {
            "sql": query.sql[:SQL_LENGTH],
            "params": query.params,
            "call_site": query.call_site,
            "duration": query.duration,
        }
        for query in sorted(queries, key=lambda query: -query.duration)[:slow_top]
    ]

    requests: defaultdict[tuple[str, int], int] = defaultdict(int)
    for query in queries:
        if query.route is not None and query.request_id is not None:
            requests[query.route, query.request_id] += 1

    routes: dict[str, RouteUsage] = {}
    for (route, _request_id), count in requests.items():
        usage = routes.setdefault(
            route, {"route": route, "requests": 0, "queries": 0, "max_per_request": 0}
        )
        usage["requests"] += 1
        usage["queries"] += count
        usage["max_per_request"] = max(usage["max_per_request"], count)

    shapes: dict[str, Shape] = {}
    for query in queries:
        shape = shapes.setdefault(normalize_sql(query.sql), {"count": 0, "time": 0.0})
        shape["count"] += 1
        shape["time"] += query.duration

    return {
        "nodeid": nodeid,
        "file": nodeid.split("::", 1)[0],
        "phases": {phase: len(phases.get(phase, [])) for phase in PHASES},
        "total": len(queries),
        "time": sum(query.duration for query in queries),
        "duplicates": duplicates,
        "n1": n1,
        "slowest": slowest,
        "routes": list(routes.values()),
        "shapes": shapes,
    }


def _top_n1(results: list[TestResult]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for result in results:
        for candidate in result["n1"]:
            entry = merged.setdefault(
                (candidate["sql"], candidate["call_site"]),
                {
                    "sql": candidate["sql"],
                    "call_site": candidate["call_site"],
                    "stack": candidate["stack"],
                    "tests": 0,
                    "max_count": 0,
                    "example": result["nodeid"],
                },
            )
            entry["tests"] += 1
            if candidate["count"] > entry["max_count"]:
                entry["max_count"] = candidate["count"]
                entry["example"] = result["nodeid"]

    return sorted(
        merged.values(), key=lambda entry: (-entry["max_count"], -entry["tests"])
    )[:REPORT_TOP]


def _top_duplicates(results: list[TestResult]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for result in results:
        for duplicate in result["duplicates"]:
            entry = merged.setdefault(
                (normalize_sql(duplicate["sql"]), duplicate["call_site"]),
                {
                    "sql": normalize_sql(duplicate["sql"]),
                    "call_site": duplicate["call_site"],
                    "tests": 0,
                    "wasted": 0,
                    "example": result["nodeid"],
                },
            )
            entry["tests"] += 1
            entry["wasted"] += duplicate["count"] - 1

    return sorted(merged.values(), key=lambda entry: -entry["wasted"])[:REPORT_TOP]


def merge_results(results: list[TestResult], meta: dict[str, Any]) -> Report:
    """
    Merge the results of all tests into a suite-wide report.

    :param results: The results of all tests (from all workers)
    :param meta: Information about the test run
    :return: The report
    """
    # The per-test statement shapes are only needed for the suite-wide aggregation
    tests = [
        {key: value for key, value in result.items() if key != "shapes"}
        for result in sorted(
            results, key=lambda result: (-result["total"], result["nodeid"])
        )
    ]

    slowest: list[dict[str, Any]] = [
        {**query, "nodeid": result["nodeid"]}
        for result in results
        for query in result["slowest"]
    ]
    slowest.sort(key=lambda query: -query["duration"])

    endpoints: dict[str, dict[str, Any]] = {}
    for result in results:
        for usage in result["routes"]:
            entry = endpoints.setdefault(
                usage["route"],
                {
                    "route": usage["route"],
                    "tests": 0,
                    "requests": 0,
                    "queries": 0,
                    "max_per_request": 0,
                },
            )
            entry["tests"] += 1
            entry["requests"] += usage["requests"]
            entry["queries"] += usage["queries"]
            entry["max_per_request"] = max(
                entry["max_per_request"], usage["max_per_request"]
            )

    files: dict[str, dict[str, Any]] = {}
    for result in results:
        entry = files.setdefault(
            result["file"], {"file": result["file"], "tests": 0, "queries": 0}
        )
        entry["tests"] += 1
        entry["queries"] += result["total"]

    shapes: dict[str, dict[str, Any]] = {}
    for result in results:
        for sql, shape in result["shapes"].items():
            entry = shapes.setdefault(
                sql, {"sql": sql, "count": 0, "time": 0.0, "tests": 0}
            )
            entry["count"] += shape["count"]
            entry["time"] += shape["time"]
            entry["tests"] += 1

    return {
        "meta": meta,
        "totals": {
            "tests": len(results),
            "queries": sum(result["total"] for result in results),
            "setup_queries": sum(result["phases"]["setup"] for result in results),
            "teardown_queries": sum(result["phases"]["teardown"] for result in results),
            "time": sum(result["time"] for result in results),
            "tests_with_n1": sum(1 for result in results if result["n1"]),
            "tests_with_duplicates": sum(
                1 for result in results if result["duplicates"]
            ),
        },
        "tests": tests,
        "top_n1": _top_n1(results),
        "top_duplicates": _top_duplicates(results),
        "slowest": slowest[:REPORT_TOP],
        "endpoints": sorted(
            endpoints.values(),
            key=lambda entry: (-entry["max_per_request"], entry["route"]),
        ),
        "files": sorted(files.values(), key=lambda entry: -entry["queries"]),
        "shapes": sorted(shapes.values(), key=lambda entry: -entry["count"])[
            :REPORT_TOP
        ],
    }
