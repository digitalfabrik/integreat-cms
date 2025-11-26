import json
from typing import Any

from django.conf import settings
from django.views.generic import TemplateView


class OpenSourceLicensesView(TemplateView):
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "imprint/open_source_licenses.html"

    def create_url_from_reference_locator(self, reference_locator: str) -> str:
        """
        Create a URL from a given reference locator.

        :param reference_locator: The reference locator string.
        """
        NPM_PREFIX = "pkg:npm/"
        NPM_URL = "https://www.npmjs.com/package"
        PIP_PREFIX = "pkg:pypi/"
        PIP_URL = "https://pypi.org/project"

        if reference_locator.startswith(NPM_PREFIX):
            package_info = reference_locator[len(NPM_PREFIX) :]
            package_name = package_info.split("@")[0]
            return f"{NPM_URL}/{package_name}"
        if reference_locator.startswith(PIP_PREFIX):
            package_info = reference_locator[len(PIP_PREFIX) :]
            package_name = package_info.split("@")[0]
            return f"{PIP_URL}/{package_name}/"
        return "#"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        SBOM_FILE_PATH = settings.SBOM_DIR + settings.SBOM_FILE_NAME

        with open(SBOM_FILE_PATH, encoding="utf-8") as file:
            data = json.load(file)

        packages = data["packages"]

        for package in packages:
            package["versionInfo"] = (
                package["versionInfo"] if package["versionInfo"] else "N/A"
            )
            package["url"] = None
            if "externalRefs" in package:
                package_managers = [
                    ref["referenceLocator"]
                    for ref in package["externalRefs"]
                    if ref["referenceCategory"] == "PACKAGE-MANAGER"
                ]
                if package_managers:
                    package["url"] = self.create_url_from_reference_locator(
                        package_managers[0]
                    )

        return {
            "packages": packages,
        }
