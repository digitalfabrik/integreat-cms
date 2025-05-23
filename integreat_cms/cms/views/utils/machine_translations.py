"""
This module contains the generalized function to build the AJAX call for the machine translation popup
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.http import JsonResponse

from ....core.utils.word_count import word_count
from ....textlab_api.utils import check_hix_score
from ...constants.machine_translatable_attributes import TRANSLATABLE_ATTRIBUTES
from ...models import Event, Page, POI

if TYPE_CHECKING:
    from typing import Literal

    from django.http import HttpRequest

logger = logging.getLogger(__name__)


def build_json_for_machine_translation(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    model_type: Literal["page", "event", "poi"],
) -> JsonResponse:
    """
    This function collects the hix score and the amount of words per content entry from the source

    :param request: The current request
    :param language_slug: The slug of the current language
    :param model_type: The according model to the different content types
    :return: A dictionary that contains the data for the machine translation popup (page id, title, amount of words and optional hix value)
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
        region=request.region,
        id__in=selected_content_ids,
    )

    filtered_content = {}
    translatable = {}
    non_translatable = {}

    source_language = request.region.get_source_language(language_slug)

    for content in selected_content:
        source_translation = content.get_translation(source_language.slug)

        content.translatable_attributes = [
            (attr, getattr(source_translation, attr))
            for attr in TRANSLATABLE_ATTRIBUTES
            if hasattr(source_translation, attr)
            and getattr(source_translation, attr)
            and not (content.do_not_translate_title and attr == "title")
        ]
        words = word_count(
            content.translatable_attributes,
        )

        if source_translation and check_hix_score(
            request,
            source_translation,
            show_message=False,
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
                "title": (
                    source_translation.title
                    if source_translation
                    else content.best_translation.title
                ),
                "words": words,
                "hix": False,
            }
            non_translatable.update({content.id: content_data})

    filtered_content = {
        "translatable": translatable,
        "non_translatable": non_translatable,
    }
    return JsonResponse(filtered_content)
