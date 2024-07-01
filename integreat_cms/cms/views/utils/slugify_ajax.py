from __future__ import annotations

import json
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.text import slugify

from ...models import EventTranslation, PageTranslation, POITranslation
from ...utils.slug_utils import generate_unique_slug

if TYPE_CHECKING:
    from typing import Literal

    from django.http import HttpRequest

    from ...utils.slug_utils import SlugKwargs


# pylint: disable=unused-argument
def slugify_ajax(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    model_type: Literal["page", "event", "poi"],
) -> JsonResponse:
    """checks the current user input for title and generates unique slug for permalink

    :param request: The current request
    :param region_slug: region identifier
    :param language_slug: language slug
    :param model_type: The type of model to generate a unique slug for, one of `event|page|poi`
    :return: unique translation slug
    :raises ~django.core.exceptions.PermissionDenied: If the user does not have the permission to access this function
    """
    required_permission = {
        "event": "cms.change_event",
        "page": "cms.change_page",
        "poi": "cms.change_poi",
    }[model_type]

    managers = {
        "event": EventTranslation,
        "page": PageTranslation,
        "poi": POITranslation,
    }

    json_data = json.loads(request.body)
    language = request.region.get_language_or_404(language_slug, only_active=True)
    model_id = json_data.get("model_id")

    manager = managers[model_type].objects
    object_instance = manager.filter(
        **{model_type: model_id, "language": language}
    ).first()

    if not (
        request.user.has_perms((required_permission,))
        or (
            model_type == "page"
            and object_instance.page
            in request.user.access_granted_pages(request.region)
        )
    ):
        raise PermissionDenied

    form_title = slugify(json_data["title"], allow_unicode=True)
    kwargs: SlugKwargs = {
        "slug": form_title,
        "manager": manager,
        "object_instance": object_instance,
        "foreign_model": model_type,
        "region": request.region,
        "language": language,
    }
    unique_slug = generate_unique_slug(**kwargs)
    return JsonResponse({"unique_slug": unique_slug})
