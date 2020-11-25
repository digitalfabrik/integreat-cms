"""
This module contains view actions for region user objects.
"""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from ...decorators import region_permission_required
from ...models import Region


@login_required
@region_permission_required
@permission_required("cms.manage_region_users", raise_exception=True)
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

    # TODO: Check permissions

    region = Region.get_current_region(request)
    user = get_user_model().objects.get(id=user_id, profile__regions=region)
    if user.regions.count == 1:
        user.delete()
        messages.success(request, _(f"User {user} was successfully deleted."))
    else:
        user.profile.regions.remove(region)
        user.profile.save()
        messages.success(
            request, _(f"User {user} was successfully removed from this region.")
        )

    return redirect("region_users", region_slug=region.slug)
