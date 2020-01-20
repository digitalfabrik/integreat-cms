"""
A view representing an instance of a accommodationnt of interest. Accommodations can be added, changed or retrieved via this view.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _

from ...decorators import region_permission_required, staff_required
from ...models import Accommodation

logger = logging.getLogger(__name__)


@login_required
@region_permission_required
@permission_required('cms.manage_accommodations', raise_exception=True)
def archive_accommodation(request, accommodation_id, region_slug, language_code):
    accommodation = Accommodation.objects.get(id=accommodation_id)

    accommodation.archived = True
    accommodation.save()

    messages.success(request, _('Accommodation was successfully archived.'))

    return redirect('accommodations', **{
                'region_slug': region_slug,
                'language_code': language_code,
    })


@login_required
@region_permission_required
@permission_required('cms.manage_accommodations', raise_exception=True)
def restore_accommodation(request, accommodation_id, region_slug, language_code):
    accommodation = Accommodation.objects.get(id=accommodation_id)

    accommodation.archived = False
    accommodation.save()

    messages.success(request, _('Accommodation was successfully restored.'))

    return redirect('accommodations', **{
                'region_slug': region_slug,
                'language_code': language_code,
    })


@login_required
@staff_required
def delete_accommodation(request, accommodation_id, region_slug, language_code):

    accommodation = Accommodation.objects.get(id=accommodation_id)
    accommodation.delete()
    messages.success(request, _('Accommodation was successfully deleted.'))

    return redirect('accommodations', **{
        'region_slug': region_slug,
        'language_code': language_code,
    })


@login_required
@region_permission_required
@permission_required('cms.manage_accommodations', raise_exception=True)
# pylint: disable=unused-argument
def view_accommodation(request, accommodation_id, region_slug, language_code):
    template_name = 'accommodations/accommodation_view.html'
    accommodation = Accommodation.objects.get(id=accommodation_id)

    accommodation_translation = accommodation.get_translation(language_code)

    if not accommodation_translation:
        raise Http404

    return render(
        request,
        template_name,
        {
            "accommodation_translation": accommodation_translation
        }
    )
