import json

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.text import slugify

from ...models import PageTranslation, EventTranslation, POITranslation
from ...utils.slug_utils import generate_unique_slug


# pylint: disable=unused-argument
def slugify_ajax(request, region_slug, language_slug, model_type):
    """checks the current user input for title and generates unique slug for permalink

    :param request: The current request
    :type request: ~django.http.HttpResponse
    :param region_slug: region identifier
    :type region_slug: str
    :param language_slug: language slug
    :type language_slug: str
    :param model_type: The type of model to generate a unique slug for, one of `event|page|poi`
    :type model_type: str
    :return: unique translation slug
    :rtype: str
    :raises ~django.core.exceptions.PermissionDenied: If the user does not have the permission to access this function
    """
    required_permission = {
        "event": "cms.change_event",
        "page": "cms.change_page",
        "poi": "cms.change_poi",
    }[model_type]
    if not request.user.has_perms((required_permission,)):
        raise PermissionDenied

    json_data = json.loads(request.body)
    form_title = slugify(json_data["title"], allow_unicode=True)
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)
    model_id = request.GET.get("model_id")

    managers = {
        "event": EventTranslation,
        "page": PageTranslation,
        "poi": POITranslation,
    }
    manager = managers[model_type].objects
    object_instance = manager.filter(
        **{model_type: model_id, "language": language}
    ).first()

    kwargs = {
        "slug": form_title,
        "manager": manager,
        "object_instance": object_instance,
        "foreign_model": model_type,
        "region": region,
        "language": language,
    }
    unique_slug = generate_unique_slug(**kwargs)
    return JsonResponse({"unique_slug": unique_slug})
