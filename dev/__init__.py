from os import environ
from pathlib import Path

is_running_in_ci = environ.get("CI") is not None

project_home = Path(__file__).resolve().parent.parent

cms_package_dir = project_home / "integreat_cms"

cms_admin_cli = cms_package_dir / "integreat-cms-cli"
