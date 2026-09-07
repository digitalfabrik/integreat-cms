# ruff: noqa: S603
# ruff: noqa: S607
# ruff: noqa: PLW1510

import sys
from subprocess import run

from dev import project_home
from dev.utils import print_info


def djlint_check(files: list[str] | None = None) -> None:
    files = files or ["."]
    print_info("➡ Checking Django templates")
    sys.exit(run(["uv", "run", "djlint", "--lint", "--quiet", *files]).returncode)


def djlint_format(files: list[str] | None = None) -> None:
    files = files or ["."]
    print_info("➡ Formatting Django templates")
    sys.exit(
        run(
            ["uv", "run", "djlint", "--reformat", "--lint", "--quiet", *files]
        ).returncode
    )


def eslint_check() -> None:
    print_info("➡ Checking JS/TS files with eslint")
    sys.exit(run(["npm", "exec", "eslint", "--", "."], cwd=project_home).returncode)


def eslint_fix() -> None:
    print_info("➡ Fixing JS/TS files with eslint")
    sys.exit(
        run(["npm", "exec", "eslint", "--", "--fix", "."], cwd=project_home).returncode
    )


def mypy() -> None:
    print_info("➡ Type checking Python sources with mypy")
    sys.exit(run(["uv", "run", "mypy", "--scripts-are-modules", "."]).returncode)


def prettier_check() -> None:
    print_info("➡ Checking files with prettier")
    sys.exit(
        run(
            ["npm", "exec", "prettier", "--", "--check", "--log-level=warn", "."],
            cwd=project_home,
        ).returncode
    )


def prettier_format() -> None:
    print_info("➡ Formatting files with prettier")
    sys.exit(
        run(
            ["npm", "exec", "prettier", "--", "--write", "--log-level=warn", "."],
            cwd=project_home,
        ).returncode
    )


def ruff_check(files: list[str] | None = None) -> None:
    files = files or ["."]
    print_info("➡ Linting and formatting Python sources with ruff")
    sys.exit(run(["uv", "run", "ruff", "check", *files]).returncode)


def ruff_format(files: list[str] | None = None) -> None:
    files = files or ["."]
    print_info("➡ Formatting Python sources with ruff")
    sys.exit(run(["uv", "run", "ruff", "format", *files]).returncode)
