"""
View to return a JSON representation of a single page. The page can
be selected via the id or the permalink.
"""
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404

from cms.models import Region
from .pages import transform_page


# pylint: disable=unused-argument
def single_page(request, region_slug, language_code):
    """
    View function returning the desired page as a JSON or a 404 if the
    requested page does not exist.

    :param request: The request that has been sent to the Django server
    :type request: ~django.http.HttpRequest

    :param region_slug: Slug defining the region
    :type region_slug: str

    :param language_code: Code to identify the desired language
    :type language_code: str

    :raises ~django.http.Http404: HTTP status 404 if the request is malformed or no page with the given id or url exists.

    :return: Return a JSON with the requested page and a HTTP status 200.
    :rtype: ~django.http.JsonResponse
    """
    region = Region.get_current_region(request)

    if request.GET.get("id"):
        page = get_object_or_404(region.pages, id=request.GET.get("id"))
        page_translation = page.get_public_translation(language_code)
        if page_translation:
            return JsonResponse(transform_page(page_translation), safe=False)

    elif request.GET.get("url"):
        # Strip leading and trailing slashes to avoid ambiguous urls
        url = request.GET.get("url").strip("/")
        # The last path component of the url is the page translation slug
        page_translation_slug = url.split("/")[-1]
        # Get page by filtering for translation slug and translation language code
        page = get_object_or_404(
            region.pages,
            translations__slug=page_translation_slug,
            translations__language__code=language_code,
        )
        # Get most recent public revision of the page
        page_translation = page.get_public_translation(language_code)
        if page_translation:
            return JsonResponse(transform_page(page_translation), safe=False)

    raise Http404("No Page matches the given url or id.")
