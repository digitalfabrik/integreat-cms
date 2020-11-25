"""
This module contains view actions for user objects.
"""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from ...decorators import staff_required


@staff_required
@login_required
@permission_required("cms.manage_admin_users", raise_exception=True)
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

    # TODO: Check permissions

    get_user_model().objects.get(id=user_id).delete()

    messages.success(request, _("User was successfully deleted"))

    return redirect("users")
