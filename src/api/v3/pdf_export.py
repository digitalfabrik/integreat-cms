"""
View to return PDF document containing the requested pages.
Single pages may be requested by url parameter, if no parameter is included all pages
related to the current region and language will be returned.
"""
import logging

from django.shortcuts import get_object_or_404

from cms.models import Region
from cms.utils.pdf_utils import generate_pdf

from ..decorators import json_response

logger = logging.getLogger(__name__)


@json_response
# pylint: disable=unused-argument
def pdf_export(request, region_slug, language_code):
    """
    View function that either returns the requested page specified by the
    url parameter or returns all pages of current region and language as PDF document
    by forwarding the request to :func:`~cms.utils.pdf_utils.generate_pdf`

    :param request: request that was sent to the server
    :type request: ~django.http.HttpRequest

    :param region_slug: Slug defining the region
    :type region_slug: str

    :param language_code: current language code
    :type language_code: str

    :return: The requested pages as PDF document (inline)
    :rtype: ~django.http.HttpResponse
    """
    region = Region.get_current_region(request)
    # Request unrestricted queryset because pdf generator performs further operations (e.g. aggregation) on the queryset
    pages = region.get_pages(return_unrestricted_queryset=True)
    if request.GET.get("url"):
        # remove leading and trailing slashed to avoid ambiguous urls
        url = request.GET.get("url").strip("/")
        # the last path component of the url is the page translation slug
        page_translation_slug = url.split("/")[-1]
        # get page by filtering for translation slug and translation language code
        page = get_object_or_404(
            pages,
            translations__slug=page_translation_slug,
            translations__language__code=language_code,
        )
        pages = page.get_descendants(include_self=True)
    return generate_pdf(region, language_code, pages)
