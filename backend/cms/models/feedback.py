from django.db import models
from cms.models.page import Page
from cms.models.site import Site
from cms.models.extra import Extra
from cms.models.event import Event


class Feedback(models.Model):
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


class SiteFeedback(Feedback):

    site = models.ForeignKey(Site)

    class Meta:
        default_permissions = ()


class PageFeedback(Feedback):

    page = models.ForeignKey(Page)

    class Meta:
        default_permissions = ()


class TechnicalFeedback(Feedback):

    page = models.ForeignKey(Page)

    class Meta:
        default_permissions = ()


class ExtraFeedback(Feedback):

    extra = models.ForeignKey(Extra)

    class Meta:
        default_permissions = ()


class EventFeedback(Feedback):

    event = models.ForeignKey(Event)

    class Meta:
        default_permissions = ()


class SearchResultFeedback(Feedback):

    searchQuery = models.CharField(max_length=1000)

    class Meta:
        default_permissions = ()
