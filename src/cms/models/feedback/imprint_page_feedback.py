from django.db import models

from .feedback import Feedback
from ..regions.region import Region

# todo: doku
class ImprintPageFeedback(Feedback):
    """
    Database model representing feedback about regions in general.

    Fields inherited from the base model :class:`~cms.models.feedback.feedback.Feedback`:

    :param id: The database id of the feedback
    :param emotion: Whether the feedback is positive or negative (choices: :mod:`cms.constants.feedback_emotions`)
    :param comment: A comment describing the feedback
    :param is_technical: Whether or not the feedback is targeted at the developers
    :param read_status: Whether or not the feedback is marked as read
    :param created_date: The date and time when the feedback was created
    :param last_updated: The date and time when the feedback was last updated

    Relationship fields:

    :param region: The region the feedback is referring to (related name: ``feedback``)
    :param feedback_ptr: A pointer to the base class
    """

    region = models.ForeignKey(
        Region, related_name="imprint_page_feedback", on_delete=models.CASCADE
    )

    class Meta:
        default_permissions = ()
