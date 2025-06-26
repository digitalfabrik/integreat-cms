from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from integreat_cms.cms.models.push_notifications.push_notification import (
    PushNotification,
)

from ...decorators import permission_required

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect


@permission_required("cms.archive_pushnotification")
def archive_push_notification(
    request: HttpRequest,
    push_notification_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Method that archives a given push notification

    :param request: The current request
    :param push_notification_id: Id of the existing push notification that is supposed to be archived
    :param region_slug: The slug of the current region
    :return: A redirection to the :class:`~integreat_cms.cms.views.push_notifications.push_notification_list_view.PushNotificationListView`
    """
    to_be_archived_pn = get_object_or_404(
        PushNotification,
        id=push_notification_id,
        regions=request.region,
    )
    to_be_archived_pn.archive()
    messages.success(
        request,
        _("Push notification {0} was successfully archived").format(to_be_archived_pn),
    )
    return redirect(
        "push_notifications",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@permission_required("cms.archive_pushnotification")
def restore_push_notification(
    request: HttpRequest,
    push_notification_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Restore given push notification

    :param request: The current request
    :param push_notification_id: The id of the push notification which should be restored
    :param region_slug: The slug of the current region
    :return: A redirection to the :class:`~integreat_cms.cms.views.push_notifications.push_notification_list_view.PushNotificationListView`
    """
    to_be_restored_pn = get_object_or_404(
        PushNotification,
        id=push_notification_id,
        regions=request.region,
    )
    to_be_restored_pn.restore()

    messages.success(
        request,
        _("Push notification {0} was successfully restored").format(to_be_restored_pn),
    )

    return redirect(
        "archived_push_notifications",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@permission_required("cms.delete_pushnotification")
def delete_push_notification(
    request: HttpRequest,
    push_notification_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Delete given push notification

    :param request: The current request
    :param push_notification_id: The id of the push notification which should be deleted
    :param region_slug: The slug of the current region
    :return: A redirection to the :class:`~integreat_cms.cms.views.push_notifications.push_notification_list_view.PushNotificationListView`
    """
    to_be_deleted_pn = get_object_or_404(
        PushNotification,
        id=push_notification_id,
        regions=request.region,
    )
    # we need to save the title in a new variable to show it in the message
    best_translation = to_be_deleted_pn.best_translation
    to_be_deleted_pn.delete()

    messages.success(
        request,
        _("Push notification {0} was successfully deleted").format(best_translation),
    )

    return redirect(
        "push_notifications",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )
