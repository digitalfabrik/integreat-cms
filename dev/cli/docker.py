# ruff: noqa: S603
# ruff: noqa: PLW1510

from subprocess import run

from dev.utils import print_info


def _log(command: list[str]) -> None:
    print_info(f"➡ Running: {' '.join(command)}")


def docker_compose_exec(
    service: str, args: list[str], *, compose_file: str | None = None
) -> None:
    command = [
        "docker",
        "compose",
        *(["-f", compose_file] if compose_file else []),
        "exec",
        service,
        *args,
    ]
    _log(command)
    run(command)


def docker_compose_up(*, compose_file: str | None = None, detach: bool = False) -> None:
    command = [
        "docker",
        "compose",
        *(["-f", compose_file] if compose_file else []),
        "up",
        "--remove-orphans",
        *(["--detach"] if detach else ["--menu"]),
    ]
    _log(command)
    run(command)


def docker_compose_down() -> None:
    command = [
        "docker",
        "compose",
        "down",
    ]
    _log(command)
    run(command)


def docker_compose_run(
    service: str,
    args: list[str],
    *,
    compose_file: str | None = None,
    deps: bool = True,
) -> None:
    command = [
        "docker",
        "compose",
        *(["-f", compose_file] if compose_file else []),
        "run",
        # "--quiet",  # Do not log anything
        "--rm",  # Remove container after execution
        "--remove-orphans",  # Remove orphan containers
        *(["--no-deps"] if not deps else []),  # Start dependant services
        service,
        *args,
    ]
    _log(command)
    run(command, check=True, text=True)
