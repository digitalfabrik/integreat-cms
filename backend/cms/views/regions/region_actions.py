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

    if not request.user.has_perm('cms.manage_regions'):
        raise PermissionDenied

    region = Region.objects.get(slug=kwargs.get('region_slug'))
    region.delete()

    messages.success(request, _('Region was successfully deleted.'))

    return redirect('regions')
