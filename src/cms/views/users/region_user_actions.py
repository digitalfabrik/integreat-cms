from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from ...decorators import region_permission_required
from ...models import Region


@login_required
@region_permission_required
def delete_region_user(request, region_slug, user_id):
    get_user_model().objects.get(
        id=user_id, profile__regions=Region.objects.get(slug=region_slug)
    ).delete()

    messages.success(request, _("User was successfully deleted."))

    return redirect("region_users", region_slug=region_slug)
