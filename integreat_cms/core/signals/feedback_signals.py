"""
This module contains signal handlers related to feedback objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cacheops import invalidate_obj
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ...cms.models import (
    EventFeedback,
    EventListFeedback,
    Feedback,
    ImprintPageFeedback,
    MapFeedback,
    OfferFeedback,
    OfferListFeedback,
    PageFeedback,
    POIFeedback,
    RegionFeedback,
    SearchResultFeedback,
)
from ..utils.decorators import disable_for_loaddata

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.base import ModelBase


@receiver(post_delete, sender=Feedback)
# pylint: disable=unused-argument
def feedback_delete_handler(sender: ModelBase, **kwargs: Any) -> None:
    r"""
    Invalidate feedback cache after feedback deletion

    :param sender: The class of the feedback that was deleted
    :param \**kwargs: The supplied keyword arguments
    """
    if kwargs.get("instance"):
        invalidate_obj(kwargs.get("instance"))


@receiver(post_save, sender=PageFeedback)
@receiver(post_save, sender=EventFeedback)
@receiver(post_save, sender=EventListFeedback)
@receiver(post_save, sender=POIFeedback)
@receiver(post_save, sender=ImprintPageFeedback)
@receiver(post_save, sender=MapFeedback)
@receiver(post_save, sender=OfferFeedback)
@receiver(post_save, sender=OfferListFeedback)
@receiver(post_save, sender=RegionFeedback)
@receiver(post_save, sender=SearchResultFeedback)
@disable_for_loaddata
# pylint: disable=unused-argument
def feedback_create_handler(sender: ModelBase, **kwargs: Any) -> None:
    r"""
    Invalidate feedback cache after feedback creation

    :param sender: The class of the feedback that was deleted
    :param \**kwargs: The supplied keyword arguments
    """
    if (instance := kwargs.get("instance")) and (
        feedback_ptr := getattr(instance, "feedback_ptr", None)
    ):
        invalidate_obj(feedback_ptr)
