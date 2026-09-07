# ruff: noqa: T201
# ruff: noqa: PLW0108

import sys
from argparse import _SubParsersAction, ArgumentParser
from collections.abc import Callable
from os import environ
from pathlib import Path
from subprocess import CalledProcessError
from typing import Literal

from argcomplete import autocomplete
from argcomplete.shell_integration import shellcode

from dev import project_home
from dev.cli import commands
from dev.cli.docker import (
    docker_compose_down,
    docker_compose_exec,
    docker_compose_run,
    docker_compose_up,
)
from dev.utils import print_error, print_warning

_project_home_docker = Path("/app")
_django_admin_cli = str(_project_home_docker / "integreat_cms" / "integreat-cms-cli")

_parser = ArgumentParser("cli")
_parser_sub = _parser.add_subparsers(title="Commands", dest="command")

# cms
_parser_cms = _parser_sub.add_parser("cms", help="CMS commands")
_parser_cms_sub = _parser_cms.add_subparsers(title="CMS commands", dest="subcommand")

# cms admin
_parser_cms_admin = _parser_cms_sub.add_parser(
    "admin", help="Run Django admin (Docker)"
)
_parser_cms_admin.add_argument(
    "admin_args", nargs="*", help="Arguments to Django admin"
)

# cms console
_parser_cms_console = _parser_cms_sub.add_parser(
    "console", help="Open a Python console in a running CMS service"
)

# cms docs
_parser_cms_docs = _parser_cms_sub.add_parser("docs", help="Create documentation")
_parser_cms_docs.add_argument(
    "--clean", help="Clean docs directory before build", action="store_true"
)

# cms pdf_cache
_parser_cms_pdf_cache = _parser_cms_sub.add_parser(
    "pdf_cache_evict", help="Evict PDF cache"
)

# cms shell
_parser_cms_shell = _parser_cms_sub.add_parser(
    "shell", help="Open a shell in a running CMS service"
)

# cms test
_parser_cms_test = _parser_cms_sub.add_parser("test", help="Run the CMS tests")
_parser_cms_test.add_argument(
    "mode", choices=("default", "changed", "ci"), help="The test mode to run"
)
_parser_cms_test.add_argument("pytest_args", nargs="*", help="Arguments to pytest")

# cms translations_check
_parser_cms_translations_check = _parser_cms_sub.add_parser(
    "translations_check", help="Check if translation files are up-to-date"
)

# cms translations_compile
_parser_cms_translations_compile = _parser_cms_sub.add_parser(
    "translations_compile", help="Create or update message translation (.po) files"
)

# completions
_parser_completions = _parser_sub.add_parser(
    "completions", help="Update completion scripts"
)

# db
_parser_db = _parser_sub.add_parser("db", help="Database commands")
_parser_db_sub = _parser_db.add_subparsers(title="Database commands", dest="subcommand")

# db fixtures_load
_parser_db_fictures_load = _parser_db_sub.add_parser(
    "fixtures_load", help="Load fixtures into the DB"
)

# dev
_parser_dev = _parser_sub.add_parser("dev", help="Development commands")
_parser_dev_sub = _parser_dev.add_subparsers(
    title="Development commands", dest="subcommand"
)

# dev up
_parser_dev_up = _parser_dev_sub.add_parser(
    "up", help="Start the development environment"
)
_parser_dev_up.add_argument(
    "--detach", action="store_true", help="Run in the background"
)

# dev down
_parser_dev_down = _parser_dev_sub.add_parser(
    "down", help="Stop the development environment"
)

# rn
_parser_rn = _parser_sub.add_parser("rn", help="Release note commands")
_parser_rn_sub = _parser_rn.add_subparsers(
    title="Release note commands", dest="subcommand"
)

# rn new
_parser_rn_new = _parser_rn_sub.add_parser("new", help="Create a new release note")
_parser_rn_new.add_argument(
    "issue", type=int, help="The issue number the release note refers to"
)
_parser_rn_new.add_argument(
    "language", choices=("en", "de"), help="The language of the given text"
)
_parser_rn_new.add_argument("text", help="The release note text")
_parser_rn_new.add_argument(
    "--overwrite", action="store_true", help="Overwrite an existing release note"
)

# rn make
_parser_rn_make = _parser_rn_sub.add_parser("make", help="Assemble release notes")
_parser_rn_make.add_argument("--all", action="store_true")
_parser_rn_make.add_argument("--format", choices=("md", "rst", "raw"), default="md")
_parser_rn_make.add_argument("--language", choices=("en", "de"), default="en")
_parser_rn_make.add_argument("--output")
_parser_rn_make.add_argument("--no-heading", action="store_true")
_parser_rn_make.add_argument("--no-subheading", action="store_true")
_parser_rn_make.add_argument("--version", dest="version")

# source
_parser_source = _parser_sub.add_parser("source", help="Source code commands")
_parser_source_sub = _parser_source.add_subparsers(
    title="Source code commands", dest="subcommand"
)

# source djlint_check
_parser_source_djlint_check = _parser_source_sub.add_parser(
    "djlint_check", help="Check Django templates"
)
_parser_source_djlint_check.add_argument(
    "files", nargs="*", default=["."], help="Files or directories to process"
)

# source djlint_format
_parser_source_djlint_format = _parser_source_sub.add_parser(
    "djlint_format", help="Format Django templates"
)
_parser_source_djlint_format.add_argument(
    "files", nargs="*", default=["."], help="Files or directories to process"
)

# source eslint_check
_parser_source_eslint_check = _parser_source_sub.add_parser(
    "eslint_check", help="Check JS/TS files with eslint"
)

# source eslint_fix
_parser_source_eslint_fix = _parser_source_sub.add_parser(
    "eslint_fix", help="Fix JS/TS files with eslint"
)

# source mypy
_parser_source_mypy = _parser_source_sub.add_parser(
    "mypy", help="Type check Python sources with mypy"
)

# source prettier_check
_parser_source_prettier_check = _parser_source_sub.add_parser(
    "prettier_check", help="Check all files handled by prettier"
)

# source prettier_format
_parser_source_prettier_format = _parser_source_sub.add_parser(
    "prettier_format", help="Format all files handled by prettier"
)

# source ruff_check
_parser_source_ruff_check = _parser_source_sub.add_parser(
    "ruff_check", help="Lint and format Python sources with ruff"
)
_parser_source_ruff_check.add_argument(
    "files", nargs="*", default=["."], help="Files or directories to process"
)

# source ruff_format
_parser_source_ruff_format = _parser_source_sub.add_parser(
    "ruff_format", help="Lint and format Python sources with ruff and fix issues"
)
_parser_source_ruff_format.add_argument(
    "files", nargs="*", default=["."], help="Files or directories to process"
)

# web
_parser_web = _parser_sub.add_parser("web", help="Web commands")
_parser_web_sub = _parser_web.add_subparsers(title="Web commands", dest="subcommand")

# web test
_parser_web_test = _parser_web_sub.add_parser("test", help="Run web tests")

autocomplete(_parser)


def _ensure_docker_compose_run(
    service: Literal["cms", "tool"],
    *,
    action: Callable[[], None],
    compose_file: str | None = None,
) -> None:
    """
    If we not already running in a service container, run the given command in one.
    Only allows a subset of services, since we can only reliably detect, if we are
    already running in a service container, where the `DOCKER_EXEC` environment variable
    is set.
    """
    if environ.get("DOCKER_EXEC") is not None:
        # Already running in Docker
        action()
    else:
        # Forward the command to a new service container
        docker_compose_run(
            service, ["uv", "run", "cli.py", *sys.argv[1:]], compose_file=compose_file
        )


def _format_command_tree(parser: ArgumentParser, indent: int = 0) -> list[str]:
    """Recursively list every subcommand of `parser`, with help text."""
    return [
        line
        for action in parser._actions
        if isinstance(action, _SubParsersAction)
        # _choices_actions carries the `help=` text passed to add_parser()
        for choice_action in action._choices_actions
        for line in [
            "  " * indent
            + (
                f"{choice_action.dest:18} {choice_action.help}"
                if choice_action.help
                else ""
            ),
            *_format_command_tree(action.choices[choice_action.dest], indent + 1),
        ]
    ]


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    args = _parser.parse_args(sys.argv[1:])

    try:
        match args.command:
            case "cms":
                match args.subcommand:
                    case "admin":
                        docker_compose_run(
                            "cms", ["uv", "run", _django_admin_cli, *args.admin_args]
                        )
                    case "console":
                        docker_compose_exec(
                            "cms",
                            [
                                "uv",
                                "run",
                                _django_admin_cli,
                                "shell",
                            ],
                        )
                    case "docs":
                        _ensure_docker_compose_run(
                            "tool", action=lambda: commands.cms.docs(clean=args.clean)
                        )
                    case "pdf_cache_evict":
                        commands.cms.pdf_cache_evict()
                    case "shell":
                        docker_compose_exec("cms", ["/bin/bash"])
                    case "test":
                        _ensure_docker_compose_run(
                            "cms",
                            action=lambda: commands.cms.test(
                                args.mode, pytest_args=args.pytest_args
                            ),
                            compose_file="docker-compose.test.yaml",
                        )
                    case "translations_check":
                        _ensure_docker_compose_run(
                            "tool", action=lambda: commands.cms.translations_check()
                        )
                    case "translations_compile":
                        _ensure_docker_compose_run(
                            "tool", action=lambda: commands.cms.translations_compile()
                        )
                    case _:
                        _parser_cms.print_help()
                        sys.exit(1)
            case "completions":
                # TODO Create and load completion scripts, alos for zsh, fish
                print(shellcode(str(project_home / "cli.py"), shell="bash"))  # noqa: S604
            case "db":
                match args.subcommand:
                    case "fixtures_load":
                        docker_compose_run(
                            "cms",
                            [
                                "uv",
                                "run",
                                _django_admin_cli,
                                "loaddata",
                                str(
                                    _project_home_docker
                                    / "integreat_cms"
                                    / "cms"
                                    / "fixtures"
                                    / "test_data.json"
                                ),
                            ],
                        )
                    case _:
                        _parser_db.print_help()
                        sys.exit(1)
            case "dev":
                match args.subcommand:
                    case "down":
                        docker_compose_down()
                    case "up":
                        docker_compose_up(detach=args.detach)
                    case _:
                        _parser_dev.print_help()
            case "rn":
                match args.subcommand:
                    case "new":
                        commands.release_notes.new(
                            issue=args.issue,
                            language=args.language,
                            text=args.text,
                            overwrite=args.overwrite,
                        )
                    case "make":
                        if args.all and args.version:
                            print_error(
                                "The option --version is incompatible with --all."
                            )
                            sys.exit(1)
                        if args.all and args.no_subheading:
                            print_error(
                                "The option --no-subheading is incompatible with --all."
                            )
                            sys.exit(1)

                        commands.release_notes.make(
                            all=args.all,
                            format=args.format,
                            language=args.language,
                            output=args.output,
                            no_heading=args.no_heading,
                            no_subheading=args.no_subheading,
                            version=args.version,
                        )
                    case _:
                        _parser_rn.print_help()
                        sys.exit(1)
            case "source":
                match args.subcommand:
                    case "djlint_check":
                        commands.source.djlint_check(args.files)
                    case "djlint_format":
                        commands.source.djlint_format(args.files)
                    case "eslint_check":
                        commands.source.eslint_check()
                    case "eslint_fix":
                        commands.source.eslint_fix()
                    case "mypy":
                        commands.source.mypy()
                    case "prettier_check":
                        commands.source.prettier_check()
                    case "prettier_format":
                        commands.source.prettier_format()
                    case "ruff_check":
                        commands.source.ruff_check(args.files)
                    case "ruff_format":
                        commands.source.ruff_format(args.files)
                    case _:
                        _parser_source.print_help()
                        sys.exit(1)
            case "web":
                match args.subcommand:
                    case "test":
                        commands.web.test()
                    case _:
                        _parser_web.print_help()
                        sys.exit(1)
            case _:
                print(
                    _parser.format_usage()
                    + "\n"
                    + "\n".join(_format_command_tree(_parser))
                )
                sys.exit(1)
    except CalledProcessError as error:
        print_error(
            f"Running '{' '.join(error.cmd)}' failed with  code {error.returncode}"
        )
        sys.exit(error.returncode)
    except KeyboardInterrupt:
        print_warning("Interrupted")
        sys.exit(1)
