"""
Module for models storing feedback from front end users
"""
from django.db import models

from .feedback import Feedback
from ..pages.page import Page


class TechnicalFeedback(Feedback):
    """
    Technical feedback on the end user app
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()
