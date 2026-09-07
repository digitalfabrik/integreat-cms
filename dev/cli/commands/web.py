# ruff: noqa: S607


from dev.cli.docker import docker_compose_run
from dev.utils import print_info


def test() -> None:
    # print_info("➡ Install web development dependencies")
    # run(["npm", "install", "--only=development"], check=True, cwd=project_home)

    print_info("➡ Running web tests")
    docker_compose_run("web", ["npm", "run", "test"])
    # run(["npm", "run", "test"], check=True, cwd=project_home)
