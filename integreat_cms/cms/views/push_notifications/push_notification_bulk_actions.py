from __future__ import annotations

from typing import TYPE_CHECKING

from integreat_cms.cms.models.push_notifications.push_notification import (
    PushNotification,
)

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ngettext, ngettext_lazy

from ...utils.stringify_list import iter_to_string
from ..bulk_action_views import BulkActionView


class PushNotificationBulkAction(BulkActionView):
    """
    View for executing contact bulk actions
    """

    #: The model of this :class:`~integreat_cms.cms.views.bulk_action_views.BulkActionView`
    model = PushNotification

    def get_extra_filters(self) -> Q:
        """
        Overwrite to filter queryset for regions since push notification can have multiple regions
        """
        return Q(regions=self.request.region)

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str:
        r"""
        Normally this function redirects to the URL namespace by getting the model name. This only works if namespace and model name are the same.
        It doesn't work in this instance, because the model is called `pushnotification`, but the URL namespace is called `push_notification`.
        Therefore we need to overwrite this function and redirect from `pushnotification` to `push_notification`.

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: url to redirect to
        """
        redirect_kwargs = {
            "region_slug": self.request.region.slug,
        }
        if "language_slug" in kwargs:
            redirect_kwargs["language_slug"] = kwargs["language_slug"]
        return reverse("push_notifications", kwargs=redirect_kwargs)


class ArchivePushNotificationsBulkAction(PushNotificationBulkAction):
    """
    Bulk action to archive multiple contacts at once
    """

    def get_permission_required(self) -> tuple[str]:
        return ("cms.archive_pushnotification",)

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
                    "The following {model_name} were successfully archived: {object_names}",
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

        return super().post(request, *args, **kwargs)


class RestorePushNotificationsBulkAction(PushNotificationBulkAction):
    """
    Bulk action to restore multiple contacts at once
    """

    def get_permission_required(self) -> tuple[str]:
        return ("cms.archive_pushnotification",)

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
                    "The following {model_name} were successfully restored: {object_names}",
                    len(restore_sucessful),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(restore_sucessful),
                    ),
                    object_names=iter_to_string(restore_sucessful),
                ),
            )

        return super().post(request, *args, **kwargs)
