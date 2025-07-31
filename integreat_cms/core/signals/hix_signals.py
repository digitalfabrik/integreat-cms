from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from django.db.models.signals import pre_save

from ...cms.models import PageTranslation
from ...cms.views.utils.hix import lookup_hix_score
from ..utils.decorators import disable_for_loaddata

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any


logger = logging.getLogger(__name__)


@disable_for_loaddata
def page_translation_save_handler(instance: PageTranslation, **kwargs: Any) -> None:
    r"""
    Calculates a hix store for a page translation before saving

    :param instance: The page translation that gets saved
    :param \**kwargs: The supplied keyword arguments
    """
    if kwargs.get("raw"):
        return

    if instance.hix_ignore or not instance.hix_enabled or not instance.content.strip():
        logger.debug(
            "HIX calculation pre save signal skipped for %r (ignored=%s, enabled=%s, empty=%s)",
            instance,
            instance.hix_ignore,
            instance.hix_enabled,
            not bool(instance.content.strip()),
        )
        instance.hix_score = None
        instance.hix_feedback = None
        return

    latest_version = instance.latest_version

    if (
        latest_version
        and latest_version.hix_score
        and latest_version.content == instance.content
    ):
        logger.debug(
            "Content of %r was not changed, copying the HIX score from the previous version: %r",
            instance,
            latest_version.hix_score,
        )
        instance.hix_score = latest_version.hix_score
        instance.hix_feedback = latest_version.hix_feedback
        return

    if data := lookup_hix_score(instance.content):
        logger.debug("Storing hix score %s for %r", data["score"], instance)
        instance.hix_score = data["score"]

        if feedback := data.get("feedback"):
            instance.hix_feedback = json.dumps(feedback)
    else:
        logger.warning("Failed to retrieve the hix data for %r", instance)


def register_listeners() -> None:
    pre_save.connect(page_translation_save_handler, sender=PageTranslation)


def unregister_listeners() -> None:
    pre_save.disconnect(page_translation_save_handler, sender=PageTranslation)


@contextmanager
def enable_listeners() -> Generator[None, None, None]:
    register_listeners()
    try:
        yield
    finally:
        unregister_listeners()


@contextmanager
def disable_listeners() -> Generator[None, None, None]:
    unregister_listeners()
    try:
        yield
    finally:
        register_listeners()


register_listeners()
