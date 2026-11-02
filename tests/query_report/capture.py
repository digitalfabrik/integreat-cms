"""
Record the database queries executed inside a block of code
"""

from __future__ import annotations

import itertools
import sys
import time
from contextlib import contextmanager, ExitStack
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from django.core.signals import request_finished, request_started
from django.db import connections
from django.urls import resolve, Resolver404

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from types import FrameType
    from typing import Any, Final

#: The repository root, used to shorten file paths in call sites
REPO_ROOT: Final = Path(__file__).resolve().parent.parent.parent
#: Files below this directory are application code
APP_DIR: Final = str(REPO_ROOT / "integreat_cms") + "/"
#: Files below this directory are tests
TESTS_DIR: Final = str(REPO_ROOT / "tests") + "/"
#: Files below this directory (except its tests) belong to this plugin and are never a call site
PLUGIN_DIR: Final = str(Path(__file__).resolve().parent) + "/"
#: The number of application frames kept per query
STACK_DEPTH: Final = 3
#: The maximum length of the stored query parameters
PARAMS_LENGTH: Final = 200

#: The URL route and id of the request currently handled by the test client
_current_request: ContextVar[tuple[str, int] | None] = ContextVar(
    "query_report_request", default=None
)
_request_ids = itertools.count(1)


@dataclass
class QueryRecord:
    """
    A single executed database query
    """

    sql: str
    params: str
    duration: float
    many: bool
    alias: str
    route: str | None
    request_id: int | None
    call_site: str
    stack: list[str]


def _format_frame(frame: FrameType) -> str:
    path = Path(frame.f_code.co_filename).relative_to(REPO_ROOT)
    return f"{path}:{frame.f_lineno} in {frame.f_code.co_name}"


def _is_plugin_file(filename: str) -> bool:
    return filename.startswith(PLUGIN_DIR) and not Path(filename).name.startswith(
        "test_"
    )


def find_call_site(frame: FrameType | None) -> tuple[str, list[str]]:
    """
    Find the code which triggered a query by walking up the stack.

    :param frame: The innermost frame to start from
    :return: The innermost application frame (or test frame if there is none)
             and up to :attr:`STACK_DEPTH` application frames
    """
    app_frames: list[str] = []
    test_frame: str | None = None
    while frame is not None and len(app_frames) < STACK_DEPTH:
        filename = frame.f_code.co_filename
        if filename.startswith(APP_DIR) and "/migrations/" not in filename:
            app_frames.append(_format_frame(frame))
        elif (
            test_frame is None
            and filename.startswith(TESTS_DIR)
            and not _is_plugin_file(filename)
        ):
            test_frame = _format_frame(frame)
            if not app_frames:
                break
        frame = frame.f_back
    if app_frames:
        return app_frames[0], app_frames
    return test_frame or "<unknown>", []


class _Recorder:
    def __init__(self, alias: str, records: list[QueryRecord]) -> None:
        self.alias = alias
        self.records = records

    def __call__(
        self,
        execute: Callable[..., Any],
        sql: str,
        params: Any,
        many: bool,
        context: dict[str, Any],
    ) -> Any:
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            duration = time.perf_counter() - start
            request = _current_request.get()
            call_site, stack = find_call_site(sys._getframe(1))
            self.records.append(
                QueryRecord(
                    sql=sql,
                    params=repr(params)[:PARAMS_LENGTH],
                    duration=duration,
                    many=many,
                    alias=self.alias,
                    route=request[0] if request else None,
                    request_id=request[1] if request else None,
                    call_site=call_site,
                    stack=stack,
                )
            )


def _on_request_started(environ: dict[str, Any] | None = None, **_: Any) -> None:
    path = (environ or {}).get("PATH_INFO", "")
    try:
        route = str(resolve(path).route)
    except Resolver404:
        route = path
    _current_request.set((route, next(_request_ids)))


def _on_request_finished(**_: Any) -> None:
    _current_request.set(None)


@contextmanager
def record_queries() -> Generator[list[QueryRecord]]:
    """
    Record all queries on all database connections while the context is active.

    :return: The list the records are appended to
    """
    records: list[QueryRecord] = []
    request_started.connect(_on_request_started, dispatch_uid="query_report")
    request_finished.connect(_on_request_finished, dispatch_uid="query_report")

    try:
        with ExitStack() as stack:
            for conn in connections.all():
                stack.enter_context(
                    conn.execute_wrapper(_Recorder(conn.alias, records))
                )
            yield records
    finally:
        request_started.disconnect(dispatch_uid="query_report")
        request_finished.disconnect(dispatch_uid="query_report")
        _current_request.set(None)
