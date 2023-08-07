"""
This module includes functions related to the social media headers API endpoint.
"""
import logging
from html import unescape

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils.html import strip_tags
from django.utils.translation import activate

from ...cms.models import PageTranslation

logger = logging.getLogger(__name__)


# pylint: disable=unused-argument
def socialmedia_headers(request, region_slug, language_slug, path):
    """
    Renders the social media headers for a single page

    :param request: The request that has been sent to the Django server
    :type request: ~django.http.HttpRequest

    :param region_slug: Slug defining the region
    :type region_slug: str

    :param language_slug: Code to identify the desired language
    :type language_slug: str

    :param path: Should be a page translation slug
    :type path: str

    :return: HTML meta headers required by social media platforms
    :rtype: ~django.template.response.TemplateResponse
    """
    region = request.region
    page_translation = PageTranslation.search(region, language_slug, path).first()
    activate(language_slug)

    if region.slug != "hallo":
        if not page_translation:
            raise Http404
        excerpt = unescape(strip_tags(page_translation.content))[:100]
        title = page_translation.title
    else:
        excerpt = (
            "hallo aschaffenburg is your digital companion for the town of Aschaffenburg. Here"
            " you can find local information, advice centres and services."
            if region == "hallo"
            else "Your local information guide with over 100 regions in Germany."
        )
        title = "Local Information for You"
    return render(
        request,
        "socialmedia_headers.html",
        {
            "title": title,
            "excerpt": excerpt,
            "platform": "hallo aschaffenburg"
            if region.slug == "hallo"
            else settings.PLATFORM_NAME,
            "path": f"https://halloaschaffenburg.de/{path}"
            if region.slug == "hallo"
            else f"{settings.WEBAPP_URL}/{path}",
            "image": settings.SOCIAL_PREVIEW_IMAGE,
        },
    )
