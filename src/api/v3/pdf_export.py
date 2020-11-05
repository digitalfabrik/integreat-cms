"""
View to return PDF document containg the requested pages.
Single pages may be requested by url parameter, if no parameter is included all pages
related to the current region and language will be returned.
"""
import logging

from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from cms.models import Region, Page
from cms.views.pages.page_actions import export_pdf

logger = logging.getLogger(__name__)


def pdf_export(request, region_slug, language_code):
    """
    View function that either returns the requested page specified by the
    GET parameter or returns all pages of current region and language as PDF document
    by manipulating the GET parameter (see :class:`django.http.QueryDict`)
    and forwarding the request to view :func:`~cms.views.pages.page_actions.export_pdf`

    :param request: The request that was sent to the server
    :type request: ~django.http.HttpRequest

    :param region_slug: Slug defining the region
    :type region_slug: str

    :param language_code: The current language code
    :type language_code: str

    :return: The requested pages as PDF document (inline)
    :rtype: ~django.http.HttpResponse
    """
    region = Region.get_current_region(request)
    # since instances of GET are immutable,
    # they must be copied before modified
    request.GET = request.GET.copy()
    if request.GET.get("url"):
        # remove leading and trailing slashed to avoid ambiguos urls
        url = request.GET.get("url").strip("/")
        # get page candidate by filtering for translation slug
        page = get_object_or_404(
            Page, region=region, translations__slug=url.split("/")[-1]
        )
        # get recent page translation
        page_translation = page.get_public_translation(language_code)
        # Check if the whole path is correct, not only the slug
        # TODO: Once we have a permalink mapping of old versions, we also have to check whether the permalink was valid in the past
        if page_translation.permalink == url:
            pages = page.get_descendants(include_self=True)
            request.GET.update({"api": pages})
        else:
            logger.error(
                "The requested url: %s does not match the permalink for this page translation: %s",
                url,
                page_translation.permalink,
            )
            return HttpResponse(
                "There exists no appropriate page for the requested url."
            )
    else:
        request.GET.update({"api": region.pages.filter(archived=False)})
    response = export_pdf(request, region_slug, language_code)
    # remove file attachment to display the pdf document inline
    response["Content-Disposition"] = response["Content-Disposition"].replace(
        "attachment; ", ""
    )
    return response
