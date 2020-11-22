"""
This module contains view actions for region objects.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from ...decorators import staff_required
from ...models import Region


@login_required
@staff_required
# pylint: disable=unused-argument
def delete_region(request, *args, **kwargs):
    """
    This view deletes a region

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param args: The supplied arguments
    :type args: list

    :param kwargs: The supplied keyword arguments
    :type kwargs: dict

    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to manage regions

    :return: A redirection to the media library
    :rtype: ~django.http.HttpResponseRedirect
    """

    if not request.user.has_perm("cms.manage_regions"):
        raise PermissionDenied

    region = Region.get_current_region(request)
    region.delete()

    messages.success(request, _("Region was successfully deleted"))

    return redirect("regions")
