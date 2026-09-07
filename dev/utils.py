# ruff: noqa: T201 No print statements in production code.

import sys


def print_error(message: str) -> None:
    print(f"\x1b[1;31m{message}\x1b[0;39m", file=sys.stderr)


def print_success(message: str) -> None:
    print(f"\x1b[1;32m{message}\x1b[0;39m")


def print_warning(message: str) -> None:
    print(f"\x1b[1;33m{message}\x1b[0;39m")


def print_info(message: str) -> None:
    print(f"\x1b[1;34m{message}\x1b[0;39m")


def print_bold(message: str) -> None:
    print(f"\x1b[1m{message}\x1b[0m")

