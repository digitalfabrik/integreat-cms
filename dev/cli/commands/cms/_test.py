#!/usr/bin/env python3

# ruff: noqa: S603
# ruff: noqa: S607

import shutil
import sys
from os import environ
from pathlib import Path
from subprocess import run
from typing import Literal

import pytest

from dev import cms_admin_cli, cms_package_dir, project_home
from dev.cli.commands.cms._pdf_cache import pdf_cache_evict
from dev.utils import print_bold, print_info, print_warning

_testmon_env = project_home / ".testmondata.docker"
_code_coverage_dir = project_home / "htmlcov"
#: Source trees that are bind-mounted from the host and imported during the test
#: run. They must be warmed before pytest-xdist spawns its workers (see
#: :func:`warm_source_cache`).
_import_roots = (cms_package_dir, project_home / "tests")


def test(
    mode: Literal["changed", "ci", "default"], pytest_args: list[str] | None = None
) -> None:
    pytest_args = pytest_args or []

    # Compile translation files so translation-dependent tests (e.g. the CSV feedback export)
    # behave deterministically. Run from inside the package directory.
    print_info("➡ Compile translation files")
    run(
        [
            cms_admin_cli,
            "compilemessages",
        ],
        check=True,
        cwd=cms_package_dir,
        timeout=60,
    )

    print_info("➡ Delete outdated code coverage reports")
    shutil.rmtree(_code_coverage_dir, ignore_errors=True)

    # Wait for the PostgreSQL service to accept connections. `depends_on` with a
    # health check already gates startup, but this makes the dependency explicit
    # and survives a restarted db container.
    print_info("➡ Waiting for database...")
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

    # Read every Python source file once so the guest filesystem cache is warm
    # before pytest-xdist spawns its worker processes.

    # Why this is necessary
    # ---------------------
    # On macOS the source tree is bind-mounted into the container through Docker
    # Desktop's virtiofs (a FUSE-based share). virtiofs does not reliably serve
    # *cold, concurrent* metadata lookups: when many freshly spawned processes
    # perform the very first ``stat``/``open`` of a not-yet-cached path at the
    # same time, some of them get a spurious ``ENOENT``. pytest-xdist starts N
    # fresh worker processes that immediately, in parallel, cold-import the whole
    # ``integreat_cms`` package tree (collecting ``tests/cms/views/view_config.py``
    # calls ``reverse()`` at import time, which pulls in the entire URLconf). The
    # spurious ``ENOENT`` then surfaces in Python as ``ModuleNotFoundError`` for a
    # module that plainly exists, and *which* module loses the race varies from
    # run to run.

    # Reading the trees once from this single parent process populates the guest
    # kernel's shared FUSE/page cache, so the workers' subsequent lookups hit warm
    # entries and never see the spurious ``ENOENT``. Native Linux (CI) is
    # unaffected because it does not go through virtiofs, but warming there is
    # cheap and harmless, so it always runs.

    # print_info("➡ Warming source cache (virtiofs cold-import workaround)")
    # for root in _import_roots:
    #     for path in root.rglob("*.py"):
    #         # A file vanishing mid-walk is irrelevant to warming the cache.
    #         with suppress(OSError):
    #             path.read_bytes()


    environ["INTEGREAT_CMS_EXTERNALNEWS_DISABLE_AUTO_REIMPORT"] = "1"
    environ["DJANGO_SETTINGS_MODULE"] = "integreat_cms.core.test_settings"

    have_verbosity = any(
        arg in ("-v", "-vv", "-vvv", "-vvvv", "-q", "--quiet") for arg in pytest_args
    )
    have_parallelism = any(
        arg.startswith("-n") or arg == "--numprocesses" for arg in pytest_args
    )
    have_testmon_file = Path(_testmon_env).is_file()

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
                        "--testmon-env",
                        str(_testmon_env),
                    ]
                    if not have_parallelism
                    # Disable testmon when running in parallel — testmon conflicts with xdist
                    # and causes sporadic User.DoesNotExist errors during fixture setup.
                    else ["-p", "no:testmon"]
                ),
                *pytest_args,
            ]
        case "changed":
            if not have_testmon_file:
                print_warning("\n➡ First run in 'changed' mode: run all tests\n")

            args += [
                *(["--quiet"] if not have_verbosity else []),
                "--testmon-env",
                str(_testmon_env),
                *(
                    # Run the tests affected by recent changes and record the new
                    # dependencies, so the next run starts from the current state.
                    # Without collecting, the database would keep describing the code as
                    # it was when it was first built and the same tests would be
                    # selected forever.
                    ["--testmon"]
                    if have_testmon_file
                    # Tell testmon to run all tests and collect data
                    else ["--testmon-noselect"]
                ),
                *pytest_args,
            ]
        case "ci":
            args += [
                "--no-testmon",
                "--numprocesses=logical",
                "--disable-warnings",
                "--cov=integreat_cms",
                "--cov-report=xml:coverage.xml",
                "--cov-fail-under=0",
                "--junitxml=test-results/junit.xml",
                "-o",
                "junit_family=xunit1",
                "--ds=integreat_cms.core.circleci_settings",
                "-v",
            ]

    print_info(f"➡ Running pytest {' '.join(args)}\n")
    exit_code = pytest.main(args)

    if _code_coverage_dir.is_dir():
        index = (_code_coverage_dir / "index.html").resolve()
        print_info(
            "➡ Open the following file in your browser to view the test coverage:\n"
        )
        print_bold(f"\tfile://{index}\n")

    sys.exit(exit_code)
