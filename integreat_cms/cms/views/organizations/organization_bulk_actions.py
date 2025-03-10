from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.utils.translation import ngettext, ngettext_lazy

from integreat_cms.cms.utils.stringify_list import iter_to_string

from ...models import Organization
from ..bulk_action_views import BulkActionView

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class OrganizationBulkAction(BulkActionView):
    """
    View for executing organization bulk actions
    """

    #: The model of this :class:`~integreat_cms.cms.views.bulk_action_views.BulkActionView`
    model = Organization


class ArchiveBulkAction(OrganizationBulkAction):
    """
    Bulk action for archiving multiple organizations
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function to archive multiple organizations at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        archive_successful = []
        archive_failed = []

        for content_object in self.get_queryset():
            if content_object.archive():
                archive_successful.append(content_object)
            else:
                archive_failed.append(content_object)

        if archive_successful:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was successfully archived.",
                    "The following {model_name} were successfully archived: {object_names}.",
                    len(archive_successful),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(archive_successful),
                    ),
                    object_names=iter_to_string(archive_successful),
                ),
            )

        if archive_failed:
            messages.error(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} couldn't be archived as it's used by a page, poi or user.",
                    "The following {model_name} couldn't be archived as they're used by a page, poi or user: {object_names}.",
                    len(archive_failed),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(archive_failed),
                    ),
                    object_names=iter_to_string(archive_failed),
                ),
            )
        return super().post(request, *args, **kwargs)


class RestoreBulkAction(OrganizationBulkAction):
    """
    Bulk action for restoring multiple organizations
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function to restore multiple organizations at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        restore_successful = []

        for content_object in self.get_queryset():
            content_object.restore()
            restore_successful.append(content_object)

        if restore_successful:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was successfully restored.",
                    "The following {model_name} were successfully restored: {object_names}.",
                    len(restore_successful),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(restore_successful),
                    ),
                    object_names=iter_to_string(restore_successful),
                ),
            )

        return super().post(request, *args, **kwargs)


class DeleteBulkAction(OrganizationBulkAction):
    """
    Bulk action for deleting multiple organizations
    """

    def get_permission_required(self) -> tuple[str]:
        r"""
        This method overwrites get_permission_required()
        :return: The needed permission to delete contacts
        """
        return (f"cms.delete_{self.model._meta.model_name}",)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function to delete multiple organizations at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        delete_successful = []
        delete_failed = []

        for content_object in self.get_queryset():
            if content_object.delete():
                delete_successful.append(content_object)
            else:
                delete_failed.append(content_object)

        if delete_successful:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was successfully deleted.",
                    "The following {model_name} were successfully deleted: {object_names}.",
                    len(delete_successful),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(delete_successful),
                    ),
                    object_names=iter_to_string(delete_successful),
                ),
            )

        if delete_failed:
            messages.error(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} couldn't be deleted as it's used by a page, poi or user.",
                    "The following {model_name} couldn't be deleted as they're used by a page, poi or user: {object_names}.",
                    len(delete_failed),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(delete_failed),
                    ),
                    object_names=iter_to_string(delete_failed),
                ),
            )
        return super().post(request, *args, **kwargs)
