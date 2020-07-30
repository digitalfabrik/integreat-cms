from django.http import JsonResponse

from cms.models import Region


def transform_page(page_translation):
    if page_translation.page.parent:
        parent = {
            "id": page_translation.page.parent.id,
            "url": page_translation.page.parent.get_translation(
                page_translation.language.code
            ).permalink,
            "path": page_translation.page.parent.get_translation(
                page_translation.language.code
            ).slug,
        }
    else:
        parent = None
    return {
        "id": page_translation.id,
        "url": page_translation.permalink,
        "path": page_translation.slug,
        "title": page_translation.title,
        "modified_gmt": page_translation.last_updated,
        "excerpt": page_translation.text,
        "content": page_translation.combined_text,
        "parent": parent,
        "order": page_translation.page.lft,  # use left edge indicator of mptt model for order
        "available_languages": page_translation.available_languages,
        "thumbnail": None,
        "hash": None,
    }


def pages(request, region_slug, language_code):
    region = Region.objects.get(slug=region_slug)
    result = []
    for page in region.pages.all():
        page_translation = page.get_public_translation(language_code)
        if page_translation:
            result.append(transform_page(page_translation))
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
