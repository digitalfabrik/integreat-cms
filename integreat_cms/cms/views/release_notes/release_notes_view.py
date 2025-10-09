from __future__ import annotations

import os
from typing import Any

from django.conf import settings
from django.views.generic.base import TemplateView

from .release_notes_context_mixin import ReleaseNotesContextMixin


class ReleaseNotesView(TemplateView, ReleaseNotesContextMixin):
    """
    View for retrieving the release notes
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "release_notes/release_notes.html"

    def does_sbom_exist_for_this_version(self) -> bool:
        """
        Check if a Software Bill of Materials (SBoM) exists for the current version.

        :return: True if an SBOM file exists for the current version, False otherwise.
        """
        file_path = settings.SBOM_DIR + settings.SBOM_FILE_NAME
        return os.path.isfile(file_path)

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        """
        Add the release notes to the context

        :param kwargs: Additional keyword arguments
        :return: The context for this view
        """
        context = super().get_context_data(**kwargs)
        sbom = self.does_sbom_exist_for_this_version()
        context["sbom"] = sbom
        return context
