"""
This module contains view actions related to the imprint.
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.http import HttpResponseNotFound
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...models import ImprintPage, ImprintPageTranslation, ImprintPageFeedback

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.delete_imprintpage")
def delete_imprint(request, region_slug):
    """
    Delete imprint object

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.http.Http404: If no imprint exists for the region

    :return: A redirection to the :class:`~integreat_cms.cms.views.imprint.imprint_form_view.ImprintFormView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = request.region

    try:
        imprint = region.imprint
    except ImprintPage.DoesNotExist as e:
        raise Http404 from e

    logger.debug("%r deleted by %r", imprint, request.user)

    imprint.delete()
    ImprintPageFeedback.objects.filter(region=region).delete()
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
    :type request: ~django.http.HttpRequest

    :param imprint_translation_id: The id of the requested imprint translation
    :type imprint_translation_id: int

    :return: A redirection to :class:`~integreat_cms.core.settings.WEBAPP_URL`
    :rtype: ~django.http.HttpResponseRedirect
    """

    imprint_translation = ImprintPageTranslation.objects.get(
        id=imprint_translation_id
    ).public_version

    if imprint_translation and not imprint_translation.page.archived:
        return redirect(settings.WEBAPP_URL + imprint_translation.get_absolute_url())
    return HttpResponseNotFound("<h1>Imprint not found</h1>")
