import logging
from contextlib import ExitStack
from pathlib import Path

import yaml
from django.conf import settings
from django.utils.translation import get_language_from_request
from django.views.generic.base import ContextMixin
from natsort import natsorted

logger = logging.getLogger(__name__)


class ReleaseNotesContextMixin(ContextMixin):
    """
    This mixin provides the release notes context (see :class:`~django.views.generic.base.ContextMixin`)
    """

    #: Whether only the latest release notes should be included
    only_latest_release = False

    def __init__(self):
        self.slice = 1 if self.only_latest_release else None

    def get_context_data(self, **kwargs):
        r"""
        Extend context by release notes

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The context dictionary
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context["release_notes"] = self.get_release_notes()
        return context

    def get_release_notes(self):
        """
        Get all release notes

        :return: The release note dict
        :rtype: dict
        """
        return {
            year.name: self.get_versions(year)
            for year in sorted(
                Path(settings.RELEASE_NOTES_DIRS).iterdir(), reverse=True
            )[: self.slice]
        }

    def get_versions(self, year):
        """
        Get all versions of one year

        :return: The version dict
        :rtype: dict
        """
        return {
            version.name: self.get_entries(version)
            for version in natsorted(year.iterdir(), reverse=True)[: self.slice]
        }

    def get_entries(self, version):
        """
        Get all entries of one version

        :return: The entry dict
        :rtype: dict
        """
        # Use exit stack to close file descriptors after list comprehension
        with ExitStack() as stack:
            return {
                note.stem: yaml.safe_load(
                    stack.enter_context(open(note, encoding="UTF-8"))
                )[get_language_from_request(self.request)]
                for note in natsorted(version.iterdir())
            }
