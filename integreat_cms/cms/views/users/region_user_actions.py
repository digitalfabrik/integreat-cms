"""
This module contains view actions for region user objects.
"""
import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...utils.welcome_mail_utils import send_welcome_mail

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.delete_user")
# pylint: disable=unused-argument
def delete_region_user(request, region_slug, user_id):
    """
    This view deletes a region user

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param user_id: The id of the user which should be deleted
    :type user_id: int

    :return: A redirection to region user list
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = request.region
    user = get_object_or_404(region.users, id=user_id)
    if user.regions.count() == 1:
        logger.info("%r deleted %r", request.user, user)
        user.delete()
        messages.success(request, _("User {} was successfully deleted.").format(user))
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
            _("User {} was successfully removed from this region.").format(user),
        )

    return redirect("region_users", region_slug=region.slug)


@require_POST
@permission_required("cms.change_user")
# pylint: disable=unused-argument
def resend_activation_link_region(request, region_slug, user_id):
    """
    Resends an activation link to a region user

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param user_id: users id to send the activation link
    :type user_id: int

    :return: A redirection to region user list
    :rtype: ~django.http.HttpResponseRedirect
    """
    region = request.region
    user = get_object_or_404(region.users, id=user_id)
    send_welcome_mail(request, user, activation=True)
    return redirect("region_users", region_slug=region.slug)
