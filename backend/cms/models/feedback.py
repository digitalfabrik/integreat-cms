"""
Module for models storing feedback from front end users
"""
from django.db import models

from .event import Event
from .extra import Extra
from .page import Page
from .region import Region


class Feedback(models.Model):
    """
    Base class for collecting feeedback from users.
    """
    EMOTION = (
        ("Pos", "Positive"),
        ("Neg", "Negative"),
        ("NA", "Not Available"),
    )
    emotion = models.CharField(max_length=3, choices=EMOTION)
    comment = models.CharField(max_length=1000)
    readStatus = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()
        permissions = (
            ('view_feedback', 'Can view feedback'),
        )


class RegionFeedback(Feedback):
    """
    General feedback for regions
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()


class PageFeedback(Feedback):
    """
    Feedback on a specific page
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()


class TechnicalFeedback(Feedback):
    """
    Technical feedback on the end user app
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()


class ExtraFeedback(Feedback):
    """
    Feedback on extras (extra model)
    """
    extra = models.ForeignKey(Extra, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()


class EventFeedback(Feedback):
    """
    Feedback on single events
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()


class SearchResultFeedback(Feedback):
    """
    Feedback on (i.e. empty) search results
    """
    searchQuery = models.CharField(max_length=1000)

    class Meta:
        default_permissions = ()
