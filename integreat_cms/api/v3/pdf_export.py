"""
View to return PDF document containing the requested pages.
Single pages may be requested by url parameter, if no parameter is included all pages
related to the current region and language will be returned.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.http import Http404
from django.views.decorators.cache import never_cache

from ...cms.models import Page
from ...cms.utils.pdf_utils import generate_pdf
from ..decorators import json_response

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


@json_response
@never_cache
# pylint: disable=unused-argument
def pdf_export(
    request: HttpRequest, region_slug: str, language_slug: str
) -> HttpResponseRedirect:
    """
    View function that either returns the requested page specified by the
    url parameter or returns all pages of current region and language as PDF document
    by forwarding the request to :func:`~integreat_cms.cms.utils.pdf_utils.generate_pdf`

    :param request: request that was sent to the server
    :param region_slug: Slug defining the region
    :param language_slug: current language slug
    :raises ~django.http.Http404: HTTP status 404 if the requested page translation cannot be found.

    :return: The redirect to the generated PDF document
    """
    region = request.region
    # Request unrestricted queryset because pdf generator performs further operations (e.g. aggregation) on the queryset
    pages = region.get_pages()
    if request.GET.get("url"):
        # remove leading and trailing slashed to avoid ambiguous urls
        url = request.GET.get("url").strip("/")
        # the last path component of the url is the page translation slug
        page_translation_slug = url.split("/")[-1]
        # get page by filtering for translation slug and translation language slug
        page = pages.filter(
            translations__slug=page_translation_slug,
            translations__language__slug=language_slug,
        ).distinct()
        if len(page) != 1:
            raise Http404("No matching page translation found for url.")
        pages = Page.get_tree(page[0]).prefetch_public_translations()
    else:
        pages = pages.prefetch_public_translations()
    return generate_pdf(region, language_slug, pages)
