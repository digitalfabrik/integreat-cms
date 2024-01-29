"""
This module contains view actions related to the imprint.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponseNotFound
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...models import ImprintPage, ImprintPageFeedback, ImprintPageTranslation

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.delete_imprintpage")
def delete_imprint(request: HttpRequest, region_slug: str) -> HttpResponseRedirect:
    """
    Delete imprint object

    :param request: The current request
    :param region_slug: The slug of the current region
    :raises ~django.http.Http404: If no imprint exists for the region

    :return: A redirection to the :class:`~integreat_cms.cms.views.imprint.imprint_form_view.ImprintFormView`
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


def expand_imprint_translation_id(
    request: HttpRequest, imprint_translation_id: int
) -> HttpResponseRedirect | HttpResponseNotFound:
    """
    Searches for an imprint translation with corresponding ID and redirects browser to web app

    :param request: The current request
    :param imprint_translation_id: The id of the requested imprint translation
    :return: A redirection to :class:`~integreat_cms.core.settings.WEBAPP_URL`
    """

    imprint_translation = ImprintPageTranslation.objects.get(
        id=imprint_translation_id
    ).public_version

    if imprint_translation and not imprint_translation.page.archived:
        return redirect(settings.WEBAPP_URL + imprint_translation.get_absolute_url())
    return HttpResponseNotFound("<h1>Imprint not found</h1>")
