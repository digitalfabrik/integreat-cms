#!/usr/bin/env -S uv run --script

# ruff: noqa: T201 No print statements in production code.
# ruff: noqa: S603

import os
import sys
from argparse import ArgumentParser
from collections.abc import Callable
from os import environ
from pathlib import Path
from subprocess import CalledProcessError, run

_project_home = Path(__file__).resolve().parent.parent
_cms_package_dir = _project_home / "integreat_cms"
_cms_admin_cli = _cms_package_dir / "integreat-cms-cli"


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


def _run() -> None:
    _print_info("➡ Compile translation files")
    run(
        [
            str(_cms_admin_cli),
            "compilemessages",
        ],
        check=True,
        cwd=_cms_package_dir,
        timeout=60,
    )

    _print_info("➡ Make migrations")
    run(
        [
            str(_cms_admin_cli),
            "makemigrations",
        ],
        check=True,
        cwd=_cms_package_dir,
        timeout=60,
    )

    _print_info("➡ Run migrations")
    run(
        [
            str(_cms_admin_cli),
            "migrate",
        ],
        check=True,
        cwd=_cms_package_dir,
        env={
            **os.environ,
            # TODO
            # Disable linkcheck listeners so loading fixtures doesn't enqueue Celery tasks to a (possibly absent) Redis broker
            "INTEGREAT_CMS_LINKCHECK_DISABLE_LISTENERS": "1",
        },
        timeout=180,
    )

    _print_info("➡ Load test data")
    run(
        [
            str(_cms_admin_cli),
            "loaddata",
            str(_cms_package_dir / "cms" / "fixtures" / "test_data.json"),
        ],
        check=True,
    )

    _print_info("➡ Run")
    run(
        [
            str(_cms_admin_cli),
            "runserver",
            "0.0.0.0:8000",
        ],
        check=True,
        cwd=_cms_package_dir,
    )


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
            "docker-compose.yaml",
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
_args = _parser.parse_args(sys.argv[1:])

try:
    _ensure_docker_compose_run(
        lambda: _run(),
    )
except CalledProcessError as error:
    _print_error(f"Running '{error.cmd}' failed with code {error.returncode}")
    sys.exit(error.returncode)
except KeyboardInterrupt:
    _print_warning("Interrupted")
    sys.exit(1)
