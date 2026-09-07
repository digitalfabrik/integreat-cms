# This is the entry point for the Docker Compose "cms" service.
# It prepares the DB and starts the Django development server.

# ruff: noqa: S603

import os
from subprocess import run

from dev import cms_admin_cli, cms_package_dir
from dev.utils import print_info

# TODO Suggest to recreate the DB on error
print_info("➡ Run DB migrations")
run(
    [cms_admin_cli, "migrate"],
    check=True,
    env={
        **os.environ,
        # TODO
        # Disable linkcheck listeners so loading fixtures doesn't enqueue Celery tasks to a (possibly absent) Redis broker
        # "INTEGREAT_CMS_LINKCHECK_DISABLE_LISTENERS": "1",
    },
)

# TODO Only do this on an empty DB
print_info("➡ Load test data")
run(
    [
        cms_admin_cli,
        "loaddata",
        cms_package_dir / "cms" / "fixtures" / "test_data.json",
    ],
    check=True,
)

print_info("➡ Start development server")
run(
    [cms_admin_cli, "runserver", "0.0.0.0:8000"],
    check=True,
)
