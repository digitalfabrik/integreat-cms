"""
The pytest plugin which records the queries of every test and writes the query report.
It is only registered if ``--query-report`` is passed (see :func:`configure_query_report`).
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from django.conf import settings
from django.db import connection

from .analysis import analyze_test, merge_results, N1_THRESHOLD
from .capture import record_queries
from .render import render_html

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any, Final

    from _pytest.terminal import TerminalReporter

    from .analysis import Report, TestResult
    from .capture import QueryRecord

#: The name the plugin is registered with
PLUGIN_NAME: Final = "query_report"
#: The default output directory
DEFAULT_DIR: Final = "tests-results/query-report"


def add_query_report_options(parser: pytest.Parser) -> None:
    """
    Register the CLI options of the query report.

    :param parser: The pytest option parser
    """
    group = parser.getgroup("query-report", "database query report")
    group.addoption(
        "--query-report",
        action="store_true",
        default=False,
        help="Record the database queries of every test and write a query report.",
    )
    group.addoption(
        "--query-report-dir",
        default=DEFAULT_DIR,
        help=f"Output directory of the query report (default: {DEFAULT_DIR}).",
    )
    group.addoption(
        "--query-report-n1-threshold",
        type=int,
        default=N1_THRESHOLD,
        help=(
            "Executions of the same statement from one call site to count as N+1 "
            f"candidate (default: {N1_THRESHOLD})."
        ),
    )


def configure_query_report(config: pytest.Config) -> None:
    """
    Register the plugin if ``--query-report`` is passed.
    The xdist controller (or a serial run) also clears the output directory before workers start.

    :param config: The pytest config
    """
    if not config.getoption("query_report"):
        return

    directory = Path(config.option.query_report_dir)
    if not hasattr(config, "workerinput"):
        shutil.rmtree(directory, ignore_errors=True)

    config.pluginmanager.register(QueryReportPlugin(config, directory), PLUGIN_NAME)


def merge_raw_results(directory: Path, meta: dict[str, Any]) -> Report:
    """
    Merge the raw results written by all workers.

    :param directory: The output directory containing the ``raw/`` results
    :param meta: Information about the test run
    :return: The merged report
    """
    results: list[TestResult] = []
    workers = 0
    for raw_file in sorted((directory / "raw").glob("*.json")):
        worker_results = json.loads(raw_file.read_text(encoding="utf-8"))
        workers += bool(worker_results)
        results.extend(worker_results)

    return merge_results(results, {**meta, "workers": workers})


class QueryReportPlugin:
    """
    Records the queries of each test phase and writes the results at the end of the session
    """

    def __init__(self, config: pytest.Config, directory: Path) -> None:
        self.config = config
        self.directory = directory
        self.n1_threshold: int = config.option.query_report_n1_threshold
        self.results: list[TestResult] = []
        self.phases: dict[str, list[QueryRecord]] = {}

    # Old-style hookwrappers: the ``yield`` never raises, so the records are stored even if the phase fails
    def _record(self, phase: str) -> Generator[None]:
        with record_queries() as records:
            yield
        self.phases[phase] = records

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item: pytest.Item) -> Generator[None]:
        yield from self._record("setup")

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item: pytest.Item) -> Generator[None]:
        yield from self._record("call")

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(
        self, item: pytest.Item, nextitem: pytest.Item | None
    ) -> Generator[None]:
        yield from self._record("teardown")

    def pytest_runtest_logfinish(self, nodeid: str) -> None:
        # xdist relays this hook to the controller, which does not run the test itself
        if not self.phases:
            return
        self.results.append(
            analyze_test(nodeid, self.phases, n1_threshold=self.n1_threshold)
        )
        self.phases = {}

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        workerinput = getattr(self.config, "workerinput", None)
        raw = self.directory / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        worker_id = workerinput["workerid"] if workerinput else "main"
        (raw / f"{worker_id}.json").write_text(
            json.dumps(self.results), encoding="utf-8"
        )
        if workerinput:
            return
        report = merge_raw_results(self.directory, self._meta())
        (self.directory / "query-report.json").write_text(
            json.dumps(report), encoding="utf-8"
        )
        (self.directory / "index.html").write_text(
            render_html(report), encoding="utf-8"
        )

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        index = self.directory / "index.html"
        if index.exists():
            terminalreporter.write_sep("-", "query report")
            terminalreporter.write_line(f"file://{index.resolve()}")

    def _meta(self) -> dict[str, Any]:
        return {
            "created": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
            "args": [str(arg) for arg in self.config.args],
            "n1_threshold": self.n1_threshold,
            "database": connection.vendor,
            "cacheops": bool(getattr(settings, "CACHEOPS_ENABLED", False))
            and "cacheops" in settings.INSTALLED_APPS,
        }
