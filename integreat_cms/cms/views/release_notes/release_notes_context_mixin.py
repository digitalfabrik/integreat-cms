from __future__ import annotations

import logging
from contextlib import ExitStack
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING

import yaml
from django.conf import settings
from django.utils.translation import get_language_from_request
from django.views.generic.base import ContextMixin
from natsort import natsorted

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class ReleaseNotesContextMixin(ContextMixin):
    """
    This mixin provides the release notes context (see :class:`~django.views.generic.base.ContextMixin`)
    """

    #: Whether only the latest release notes should be included
    only_latest_release = False

    def __init__(self) -> None:
        self.slice = 1 if self.only_latest_release else None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Extend context by release notes

        :param \**kwargs: The supplied keyword arguments
        :return: The context dictionary
        """
        context = super().get_context_data(**kwargs)
        context["release_notes"] = self.get_release_notes()
        return context

    def get_release_notes(self) -> dict[str, dict[str, dict[str, str]]]:
        """
        Get all release notes

        :return: The release note dict
        """
        return {
            year.name: self.get_versions(year)
            for year in sorted(
                Path(settings.RELEASE_NOTES_DIRS).iterdir(), reverse=True
            )[: self.slice]
        }

    def get_versions(self, year: Path | PosixPath) -> dict[str, dict[str, str]]:
        """
        Get all versions of one year

        :return: The version dict
        """
        return {
            version.name: self.get_entries(version)
            for version in natsorted(year.iterdir(), reverse=True)[: self.slice]
        }

    def get_entries(self, version: Path | PosixPath) -> dict[str, str]:  # type: ignore[return]
        """
        Get all entries of one version

        :return: The entry dict
        """
        # Use exit stack to close file descriptors after list comprehension
        with ExitStack() as stack:
            return {
                note.stem: yaml.safe_load(
                    stack.enter_context(open(note, encoding="UTF-8"))
                )[get_language_from_request(self.request)]
                for note in natsorted(version.iterdir())
            }
