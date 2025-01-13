"""
This module contains signal handlers related to contact objects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.db.models.signals import post_save
from django.dispatch import receiver
from linkcheck.listeners import check_instance_links

from ...cms.models import EventTranslation, PageTranslation, POITranslation
from ..utils.decorators import disable_for_loaddata

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing import Any


@receiver(post_save, sender=PageTranslation)
@disable_for_loaddata
def check_page_translation_links(
    sender: PageTranslation, instance: PageTranslation, **kwargs: Any
) -> None:
    r"""
    Update all links contained in the PageTranslation

    :param sender: The model class the signal applies to
    :param instance: The page translation that gets saved
    :param \**kwargs: The supplied keyword arguments
    """
    logger.error('Updating all links contained in the PageTranslation "%r".', instance)
    check_instance_links(sender, instance, **kwargs)


@receiver(post_save, sender=EventTranslation)
@disable_for_loaddata
def check_event_translation_links(
    sender: EventTranslation, instance: EventTranslation, **kwargs: Any
) -> None:
    r"""
    Update all links contained in the EventTranslation

    :param sender: The model class the signal applies to
    :param instance: The event translation that gets saved
    :param \**kwargs: The supplied keyword arguments
    """
    logger.error('Updating all links contained in the EventTranslation "%r".', instance)
    check_instance_links(sender, instance, **kwargs)


@receiver(post_save, sender=POITranslation)
@disable_for_loaddata
def check_poi_translation_links(
    sender: POITranslation, instance: POITranslation, **kwargs: Any
) -> None:
    r"""
    Update all links contained in the POITranslation

    :param sender: The model class the signal applies to
    :param instance: The POI translation that gets saved
    :param \**kwargs: The supplied keyword arguments
    """
    logger.error('Updating all links contained in the POITranslation "%r".', instance)
    check_instance_links(sender, instance, **kwargs)
