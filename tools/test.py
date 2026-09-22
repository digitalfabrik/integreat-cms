#!/usr/bin/env -S uv run --script

# ruff: noqa: T201 No print statements in production code.
# ruff: noqa: S603
# ruff: noqa: S607

import sys
from argparse import ArgumentParser
from collections.abc import Callable
from os import environ
from pathlib import Path
from shutil import rmtree
from subprocess import CalledProcessError, run
from typing import Literal

_project_home = Path(__file__).resolve().parent.parent
_cms_package_dir = _project_home / "integreat_cms"
_cms_admin_cli = _cms_package_dir / "integreat-cms-cli"
_test_results_dir = _project_home / "test-results"
_testmon_env = _test_results_dir / "testmondata.docker"
_test_coverage_html_dir = _test_results_dir / "coverage"
_settings_module_default = "integreat_cms.core.test_settings"


def _print_bold(message: str) -> None:
    print(f"\x1b[1m{message}\x1b[0m")


def _print_error(message: str) -> None:
    print(f"\x1b[1;31m{message}\x1b[0;39m", file=sys.stderr)


def _print_success(message: str) -> None:
    print(f"\x1b[1;32m{message}\x1b[0;39m")


def _print_warning(message: str) -> None:
    print(f"\x1b[1;33m{message}\x1b[0;39m")


def _print_info(message: str) -> None:
    print(f"\x1b[1;34m{message}\x1b[0;39m")


def _test(
    mode: Literal["changed", "ci", "coverage", "default"],
    pytest_args: list[str] | None = None,
) -> None:
    import pytest

    pytest_args = pytest_args or []

    # Compile translation files so translation-dependent tests (e.g. the CSV feedback export)
    # behave deterministically. Run from inside the package directory.
    _print_info("➡ Compile translation files")
    run(
        [
            _cms_admin_cli,
            "compilemessages",
        ],
        check=True,
        cwd=_cms_package_dir,
        timeout=60,
    )

    # Wait for the PostgreSQL service to accept connections. `depends_on` with a
    # health check already gates startup, but this makes the dependency explicit
    # and survives a restarted db container.
    _print_info("➡ Waiting for database...")
    db_host = environ.get("INTEGREAT_CMS_DB_HOST", "")
    db_port = environ.get("INTEGREAT_CMS_DB_PORT", "")
    db_user = environ.get("INTEGREAT_CMS_DB_USER", "")
    db_name = environ.get("INTEGREAT_CMS_DB_NAME", "")
    run(
        [
            "pg_isready",
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "-d",
            db_name,
            "-t",
            "60",
        ],
        check=True,
        timeout=10,
    )

    have_verbosity = any(
        arg in ("-v", "-vv", "-vvv", "-vvvv", "-q", "--quiet") for arg in pytest_args
    )
    have_parallelism = any(
        arg.startswith("-n") or arg == "--numprocesses" for arg in pytest_args
    )

    args = [
        "--color=yes",
        "--disable-warnings",  # TODO Warnings should never be swallowed and always heeded
    ]

    match mode:
        case "default":
            args += [
                *(["--quiet"] if not have_verbosity else []),
                *(
                    # Serial mode (verbose): safe to use testmon
                    [
                        "--numprocesses=logical",
                        "--testmon-noselect",
                        f"--testmon-env={_testmon_env}",
                    ]
                    if not have_parallelism
                    # Disable testmon when running in parallel — testmon conflicts with xdist
                    # and causes sporadic User.DoesNotExist errors during fixture setup.
                    else ["-p", "no:testmon"]
                ),
                "--cov=integreat_cms",
                "--cov-report=html",
                f"--ds={_settings_module_default}",
                *pytest_args,
            ]
        case "changed":
            testmon_file_exists = Path(_testmon_env).is_file()

            if not testmon_file_exists:
                _print_warning("➡ First run in 'changed' mode: run all tests")

            args += [
                *(["--quiet"] if not have_verbosity else []),
                f"--testmon-env={_testmon_env}",
                *(
                    # Run the tests affected by recent changes and record the new
                    # dependencies, so the next run starts from the current state.
                    # Without collecting, the database would keep describing the code as
                    # it was when it was first built and the same tests would be
                    # selected forever.
                    ["--testmon"]
                    if testmon_file_exists
                    # Tell testmon to run all tests and collect data
                    else ["--testmon-noselect"]
                ),
                f"--ds={_settings_module_default}",
                *pytest_args,
            ]
        case "coverage":
            _print_info("➡ Delete outdated code coverage reports")
            rmtree(_test_coverage_html_dir, ignore_errors=True)

            args += [
                *(["--quiet"] if not have_verbosity else []),
                "--cov=integreat_cms",
                f"--cov-report=html:{_test_results_dir / 'coverage'}",
            ]
        case "ci":
            args += [
                "--no-testmon",
                "--numprocesses=logical",
                f"--cov-report=xml:{_test_results_dir / 'coverage.xml'}",
                "--cov=integreat_cms",
                "--cov-fail-under=0",
                f"--junitxml={_test_results_dir / 'junit' / 'junit.xml'}",
                "--override-ini=junit_family=xunit1",
                "--ds=integreat_cms.core.circleci_settings",
                "-v",
            ]

    _print_info(f"➡ Running pytest {' '.join(args)}\n")
    exit_code = pytest.main(args)

    if (
        mode == "coverage"
        and (
            coverage_html_index_file := _test_coverage_html_dir / "index.html"
        ).exists()
    ):
        _print_info(
            "➡ Open the following file in your browser to view the test coverage:\n"
        )
        _print_bold(f"\tfile://{coverage_html_index_file}\n")

    sys.exit(exit_code)


def _ensure_docker_compose_run(
    action: Callable[[], None],
) -> None:
    """
    If we not already running in a service container, run the given command in one.
    """
    if environ.get("DOCKER_EXEC") is not None:
        # Already running in Docker
        action()
    else:
        # Forward the command to a new service container
        command = [
            "docker",
            "compose",
            "-f",
            "docker-compose.test.yaml",
            "run",
            "--rm",  # Remove container after execution
            "--remove-orphans",  # Remove orphan containers
            "cms",
            "uv",
            "run",
            "/app/tools/test.py",
            *sys.argv[1:],
        ]
        _print_info(f"➡ Running: {' '.join(command)}")
        run(command, check=True, text=True)


_parser = ArgumentParser("test.py")
_parser.add_argument(
    "mode",
    choices=("changed", "ci", "coverage", "default"),
    default="default",
    help="The test mode to run",
)
_parser.add_argument("pytest_args", nargs="*", help="Arguments to pytest")

_args = _parser.parse_args(sys.argv[1:])

try:
    _ensure_docker_compose_run(
        lambda: _test(
            _args.mode,
            pytest_args=_args.pytest_args,
        ),
    )
except CalledProcessError as error:
    _print_error(f"Running '{error.cmd}' failed with code {error.returncode}")
    sys.exit(error.returncode)
except KeyboardInterrupt:
    _print_warning("Interrupted")
    sys.exit(1)
