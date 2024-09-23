from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django.views.decorators.cache import never_cache
from django.views.generic.list import MultipleObjectMixin

from integreat_cms.cms.utils.stringify_list import iter_to_string

from ...models import Organization
from ..bulk_action_views import BulkActionView
from .organization_actions import archive, delete, restore

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse
    from django.http.response import HttpResponseRedirect

logger = logging.getLogger(__name__)


class OrganizationBulkActionMixin(MultipleObjectMixin):
    """
    Mixin for organization bulk actions
    """

    #: The model of this :class:`~integreat_cms.cms.views.bulk_action_views.BulkActionView`
    model = Organization


class ArchiveBulkAction(OrganizationBulkActionMixin, BulkActionView):
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
        archive_unchanged = []
        archive_failed = []
        region = request.region

        for content_object in self.get_queryset():
            organization = get_object_or_404(region.organizations, id=content_object.id)
            if content_object.archived:
                archive_unchanged.append(content_object.name)
            if organization.archive():
                archive_successful.append(content_object.name)
            else:
                archive_failed.append(content_object.name)

        if archive_successful:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was succesfully archived.",
                    "The following {model_name_plural} were succesfully archived: {object_names}.",
                    len(archive_successful),
                ).format(
                    model_name=self.model._meta.verbose_name.title(),
                    model_name_plural=self.model._meta.verbose_name_plural,
                    object_names=iter_to_string(archive_successful),
                ),
            )
        return super().post(request, *args, **kwargs)


class RestoreBulkAction(OrganizationBulkActionMixin, BulkActionView):
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
        return super().post(request, *args, **kwargs)


class DeleteBulkAction(OrganizationBulkActionMixin, BulkActionView):
    """
    Bulk action for deleting multiple organizations
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function to delete multiple organizations at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        return super().post(request, *args, **kwargs)
