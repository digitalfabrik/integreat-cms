from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from cacheops import invalidate_obj

from ..models import (
    Feedback,
    EventFeedback,
    EventListFeedback,
    PageFeedback,
    POIFeedback,
    ImprintPageFeedback,
    MapFeedback,
    OfferFeedback,
    OfferListFeedback,
    RegionFeedback,
    SearchResultFeedback,
)


@receiver(post_delete, sender=Feedback)
# pylint: disable=unused-argument
def feedback_delete_handler(sender, **kwargs):
    r"""
    Invalidate feedback cache after feedback deletion

    :param sender: The class of the feedback that was deleted
    :type sender: type

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict
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
# pylint: disable=unused-argument
def feedback_create_handler(sender, **kwargs):
    r"""
    Invalidate feedback cache after feedback creation

    :param sender: The class of the feedback that was deleted
    :type sender: type

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict
    """
    if kwargs.get("instance") and hasattr(kwargs.get("instance"), "feedback_ptr"):
        invalidate_obj(kwargs.get("instance").feedback_ptr)
