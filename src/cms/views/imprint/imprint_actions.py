"""
This module contains view actions related to the imprint.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.http import HttpResponseNotFound

from backend.settings import WEBAPP_URL
from ...decorators import region_permission_required, staff_required
from ...models import Region, ImprintPage, ImprintPageTranslation

logger = logging.getLogger(__name__)


@login_required
@region_permission_required
@permission_required("cms.manage_imprint", raise_exception=True)
def archive_imprint(request, region_slug):
    """
    Archive imprint object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.http.Http404: If no imprint exists for the region

    :return: A redirection to the :class:`~cms.views.imprint.imprint_view.ImprintView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)

    try:
        imprint = region.imprint
    except ImprintPage.DoesNotExist as e:
        raise Http404 from e

    imprint.archived = True
    imprint.save()

    logger.debug("%r archived by %r", imprint, request.user.profile)
    messages.success(request, _("Imprint was successfully archived"))

    return redirect(
        "edit_imprint",
        **{
            "region_slug": region_slug,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.manage_imprint", raise_exception=True)
def restore_imprint(request, region_slug):
    """
    Restore imprint object (set ``archived=False``)

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.http.Http404: If no imprint exists for the region

    :return: A redirection to the :class:`~cms.views.imprint.imprint_view.ImprintView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)

    try:
        imprint = region.imprint
    except ImprintPage.DoesNotExist as e:
        raise Http404 from e

    imprint.archived = False
    imprint.save()

    logger.debug("%r restored by %r", imprint, request.user.profile)
    messages.success(request, _("Imprint was successfully restored"))

    return redirect(
        "edit_imprint",
        **{
            "region_slug": region_slug,
        },
    )


@login_required
@staff_required
@permission_required("cms.manage_imprint", raise_exception=True)
def delete_imprint(request, region_slug):
    """
    Delete imprint object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.http.Http404: If no imprint exists for the region

    :return: A redirection to the :class:`~cms.views.imprint.imprint_view.ImprintView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)

    try:
        imprint = region.imprint
    except ImprintPage.DoesNotExist as e:
        raise Http404 from e

    logger.debug("%r deleted by %r", imprint, request.user.profile)

    imprint.delete()
    messages.success(request, _("Imprint was successfully deleted"))

    return redirect(
        "edit_imprint",
        **{
            "region_slug": region_slug,
        },
    )


def expand_imprint_translation_id(request, imprint_translation_id):
    """
    Searches for an imprint translation with corresponding ID and redirects browser to web app

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param imprint_translation_id: The id of the requested imprint translation
    :type imprint_translation_id: int

    :return: A redirection to :class:`~backend.settings.WEBAPP_URL`
    :rtype: ~django.http.HttpResponseRedirect
    """

    imprint_translation = ImprintPageTranslation.objects.get(
        id=imprint_translation_id
    ).latest_public_revision

    if imprint_translation and not imprint_translation.page.archived:
        return redirect(WEBAPP_URL + imprint_translation.get_absolute_url())
    return HttpResponseNotFound("<h1>Imprint not found</h1>")
