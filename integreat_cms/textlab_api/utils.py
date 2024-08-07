"""
This module contains helpers for the TextLab API client
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

    from integreat_cms.cms.models.events.event_translation import EventTranslation
    from integreat_cms.cms.models.pages.page_translation import PageTranslation
    from integreat_cms.cms.models.pois.poi_translation import POITranslation

logger = logging.getLogger(__name__)


def check_hix_score(
    request: HttpRequest,
    source_translation: EventTranslation | (PageTranslation | POITranslation),
    show_message: bool = True,
) -> bool:
    """
    Check whether the required HIX score is met and it is not ignored

    :param request: The current request
    :param source_translation: The source translation
    :param show_message: whether the massage should be shown to users.
    :return: Whether the HIX constraints are valid
    """
    if not source_translation.hix_enabled:
        return True
    if not source_translation.hix_sufficient_for_mt:
        if show_message:
            messages.error(
                request,
                _(
                    'HIX score {:.2f} of "{}" is too low for machine translation (minimum required: {})'
                ).format(
                    source_translation.hix_score,
                    source_translation,
                    settings.HIX_REQUIRED_FOR_MT,
                ),
            )
        return False
    if source_translation.hix_ignore:
        if show_message:
            messages.error(
                request,
                _(
                    'Machine translations are disabled for "{}", because its HIX value is ignored'
                ).format(
                    source_translation.title,
                ),
            )
        return False
    logger.debug(
        "HIX score %.2f of %r is sufficient for machine translation",
        source_translation.hix_score,
        source_translation,
    )
    return True


# Mapping between fields in Textlab API response containing feedback data
# and the corresponding category names used in the CMS
textlab_api_feedback_categories = {
    "moreSentencesInClauses": "nested-sentences",
    "moreSentencesInWords": "long-sentences",
    "moreWordsInLetters": "long-words",
    "countPassiveVoiceInSentence": "passive-voice-sentences",
    "countInfinitiveConstructions": "infinitive-constructions",
    "countNominalStyle": "nominal-sentences",
    "countFutureTenseInSentence": "future-tense-sentences",
}


def format_hix_feedback(response: dict) -> list[dict[str, Any]]:
    """
    Format HIX feedback from Textlab, so it can be well handled in the front end

    :param response: The response from the Textlab

    :return: count for each feedback category
    """
    feedback_details = [
        {"category": cms_name, "result": len(response.get(textlab_name, []))}
        for textlab_name, cms_name in textlab_api_feedback_categories.items()
    ]

    abbreviations_total = 0
    if abbreviations := dict_path(response, ["dataTerms", "1289", "result"]):
        abbreviations_total = sum(len(i.get("length")) for i in abbreviations)
    feedback_details.append(
        {
            "category": "abbreviations",
            "result": abbreviations_total,
        }
    )
    return feedback_details


def dict_path(data: dict, path: list[str]) -> Any:
    """
    Resolves a path in the given data dictionary and returns the value
    :param data: The data dictionary to get the value from
    :param path: The path to lookup
    :return: The result of the lookup in the dictionary
    """
    match path:
        case []:
            return data
        case [first, *rest]:
            if not (value := data.get(first)):
                return value
            return dict_path(value, rest)
