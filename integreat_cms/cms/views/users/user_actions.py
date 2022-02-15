"""
This module contains view actions for user objects.
"""
import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...utils.welcome_mail_utils import send_welcome_mail

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.delete_user")
def delete_user(request, user_id):
    """
    This view deletes a user

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param user_id: The id of the user which should be deleted
    :type user_id: int

    :return: A redirection to user list
    :rtype: ~django.http.HttpResponseRedirect
    """

    user = get_object_or_404(get_user_model(), id=user_id)
    logger.info("%r deleted %r", request.user, user)
    user.delete()

    messages.success(request, _("User was successfully deleted"))

    return redirect("users")


@require_POST
@permission_required("cms.change_user")
def resend_activation_link(request, user_id):
    """
    Resends an activation link to an user

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param user_id: users id to send the activation link
    :type user_id: int

    :return: A redirection to region user list
    :rtype: ~django.http.HttpResponseRedirect
    """
    user = get_object_or_404(get_user_model(), id=user_id)
    send_welcome_mail(request, user, activation=True)
    return redirect("users")
