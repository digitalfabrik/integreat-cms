"""
This module contains signal handlers related to contact objects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.db.models.signals import post_save
from django.dispatch import receiver

from ...cms.models import Contact
from ...cms.utils.content_utils import clean_content
from ..utils.decorators import disable_for_loaddata

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing import Any


@receiver(post_save, sender=Contact)
@disable_for_loaddata
def contact_save_handler(instance: Contact, **kwargs: Any) -> None:
    r"""
    Update contact details in content objects after changing contact details

    :param instance: The page translation that gets saved
    :param \**kwargs: The supplied keyword arguments
    """
    referring_objects = (
        list(instance.referring_page_translations)
        + list(instance.referring_poi_translations)
        + list(instance.referring_event_translations)
    )
    for referrer in referring_objects:
        logger.debug("Updating %r, since if references %r.", referrer, instance)
        referrer.content = clean_content(referrer.content, referrer.language.slug)
        referrer.save(update_fields=["content"])
