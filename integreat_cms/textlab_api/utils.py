"""
This module contains helpers for the TextLab API client
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


def check_hix_score(request, source_translation, show_message=True):
    """
    Check whether the required HIX score is met and it is not ignored

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param source_translation: The source translation
    :type source_translation: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation

    :param show_message: whether the massage should be shown to users.
    :type show_message: bool

    :return: Whether the HIX constraints are valid
    :rtype: bool
    """
    if not source_translation.hix_enabled:
        return True
    if not source_translation.hix_sufficient_for_mt:
        logger.debug(
            "HIX score %.2f of %r is too low for machine translation (minimum required: %.1f)",
            source_translation.hix_score,
            source_translation,
            settings.HIX_REQUIRED_FOR_MT,
        )
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
        logger.debug(
            "Machine translations are disabled for %r, because its HIX value is ignored",
            source_translation,
        )
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
