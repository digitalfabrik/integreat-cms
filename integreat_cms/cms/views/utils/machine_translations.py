"""
This module contains the generalized function to build the AJAX call for the machine translation popup
"""
import json
import logging

from django.http import JsonResponse

from ....textlab_api.utils import check_hix_score
from ...models import Event, Page, POI

logger = logging.getLogger(__name__)


# pylint: disable=unused-argument, too-many-locals
def build_json_for_machine_translation(request, region_slug, language_slug, model_type):
    """
    This function collects the hix score and the amount of words per content entry from the source

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: slug of the according region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :param model_type: The according model to the different content types
    :type model_type: ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel

    :return: A dictionary that contains the data for the machine translation popup (page id, title, amount of words and optional hix value)
    :rtype: dict
    """

    model_types = {
        "event": Event,
        "page": Page,
        "poi": POI,
    }

    try:
        selected_content_ids = json.loads(request.body.decode("utf-8"))
    except json.decoder.JSONDecodeError as e:
        logger.warning("Malformed request body! %r", e)
        selected_content_ids = []
    selected_content = model_types[model_type].objects.filter(
        region=request.region, id__in=selected_content_ids
    )

    filtered_content = {}
    translatable = {}
    non_translatable = {}

    source_language = request.region.get_source_language(language_slug)

    for content in selected_content:
        source_translation = content.get_translation(source_language.slug)
        words = (
            len(source_translation.content.split())
            + len(source_translation.title.split())
            if source_translation
            else 0
        )

        if source_translation and check_hix_score(
            request, source_translation, show_message=False
        ):
            content_data = {
                "id": content.id,
                "title": source_translation.title,
                "words": words,
                "hix": True,
            }
            translatable.update({content.id: content_data})
        else:
            content_data = {
                "id": content.id,
                "title": source_translation.title
                if source_translation
                else content.best_translation.title,
                "words": words,
                "hix": False,
            }
            non_translatable.update({content.id: content_data})

    filtered_content = {
        "translatable": translatable,
        "non_translatable": non_translatable,
    }
    return JsonResponse(filtered_content)
