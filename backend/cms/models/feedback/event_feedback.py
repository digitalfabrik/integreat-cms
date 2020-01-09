"""
Module for models storing feedback from front end users
"""
from django.db import models

from .feedback import Feedback
from ..events.event import Event


class EventFeedback(Feedback):
    """
    Feedback on single events
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()
