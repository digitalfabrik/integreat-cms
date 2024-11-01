from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.db.models import Q
from django.utils.translation import ngettext_lazy

from ...models import Contact
from ...utils.stringify_list import iter_to_string
from ..bulk_action_views import BulkActionView

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class ContactBulkAction(BulkActionView):
    """
    View for executing contact bulk actions
    """

    #: The model of this :class:`~integreat_cms.cms.views.bulk_action_views.BulkActionView`
    model = Contact

    def get_extra_filters(self) -> Q:
        """
        Overwrite to filter queryset for region of the location since contact gets its region from location
        """
        return Q(location__region=self.request.region)


class ArchiveContactBulkAction(ContactBulkAction):
    """
    Bulk action to archive multiple contacts at once
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Archive multiple contacts at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """

        archive_successful = []

        for content_object in self.get_queryset():
            content_object.archive()
            archive_successful.append(content_object)

        if archive_successful:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was successfully archived.",
                    "The following {model_name_plural} were successfully archived: {object_names}",
                    len(archive_successful),
                ).format(
                    model_name=self.model._meta.verbose_name.title(),
                    model_name_plural=self.model._meta.verbose_name_plural,
                    object_names=iter_to_string(archive_successful),
                ),
            )

        return super().post(request, *args, **kwargs)


class RestoreContactBulkAction(ContactBulkAction):
    """
    Bulk action to restore multiple contacts at once
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function to restore multiple contacts at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        restore_sucessful = []
        for content_object in self.get_queryset():
            content_object.restore()
            restore_sucessful.append(content_object)

        if restore_sucessful:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was successfully restored.",
                    "The following {model_name_plural} were successfully restored: {object_names}",
                    len(restore_sucessful),
                ).format(
                    model_name=self.model._meta.verbose_name.title(),
                    model_name_plural=self.model._meta.verbose_name_plural,
                    object_names=iter_to_string(restore_sucessful),
                ),
            )

        return super().post(request, *args, **kwargs)


class DeleteContactBulkAction(ContactBulkAction):
    """
    Bulk action to delete multiple contacts at once
    """

    def get_permission_required(self) -> tuple[str]:
        r"""
        This method overwrites get_permission_required()

        :return: The needed permission to delete contacts
        """
        return (f"cms.delete_{self.model._meta.model_name}",)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function to delete multiple contacts at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        delete_sucessful = []
        for content_object in self.get_queryset():
            content_object.delete()
            delete_sucessful.append(content_object)

        if delete_sucessful:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was successfully deleted.",
                    "The following {model_name_plural} were successfully deleted: {object_names}",
                    len(delete_sucessful),
                ).format(
                    model_name=self.model._meta.verbose_name.title(),
                    model_name_plural=self.model._meta.verbose_name_plural,
                    object_names=iter_to_string(delete_sucessful),
                ),
            )

        return super().post(request, *args, **kwargs)
