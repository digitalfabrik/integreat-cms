"""
This module contains view actions for region user objects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...utils.welcome_mail_utils import send_welcome_mail

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.delete_user")
def delete_region_user(
    request: HttpRequest,
    region_slug: str,  # pylint: disable=unused-argument
    user_id: int,
) -> HttpResponseRedirect:
    """
    This view deletes a region user

    :param request: The current request
    :param region_slug: The slug of the current region
    :param user_id: The id of the user which should be deleted
    :return: A redirection to region user list
    """

    region = request.region
    user = get_object_or_404(region.region_users, id=user_id)

    if user.regions.count() == 1:
        # Mark feedback read by the user as unread to prevent IntegrityError
        user.feedback.update(read_by=None)

        user.delete()
        logger.info("%r deleted %r", request.user, user)
        messages.success(
            request,
            _('Account "{}" was successfully deleted.').format(user.full_user_name),
        )
    else:
        user.regions.remove(region)
        user.save()
        logger.info(
            "%r removed %r from %r",
            request.user,
            user,
            region,
        )
        messages.success(
            request,
            _('Account "{}" was successfully removed from this region.').format(
                user.full_user_name
            ),
        )

    return redirect("region_users", region_slug=region.slug)


@require_POST
@permission_required("cms.change_user")
def resend_activation_link_region(
    request: HttpRequest,
    region_slug: str,  # pylint: disable=unused-argument
    user_id: int,
) -> HttpResponseRedirect:
    """
    Resends an activation link to a region user

    :param request: The current request
    :param region_slug: The slug of the current region
    :param user_id: users id to send the activation link
    :return: A redirection to region user list
    """
    region = request.region
    user = get_object_or_404(region.region_users, id=user_id)
    send_welcome_mail(request, user, activation=True)
    return redirect("region_users", region_slug=region.slug)
