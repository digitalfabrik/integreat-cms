"""
Module for models storing feedback from front end users
"""
from django.db import models

from .feedback import Feedback
from ..extras.extra import Extra


class ExtraFeedback(Feedback):
    """
    Feedback on extras (extra model)
    """
    extra = models.ForeignKey(Extra, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()
