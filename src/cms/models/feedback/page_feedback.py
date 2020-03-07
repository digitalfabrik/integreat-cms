"""
Module for models storing feedback from front end users
"""
from django.db import models

from .feedback import Feedback
from ..pages.page import Page


class PageFeedback(Feedback):
    """
    Feedback on a specific page
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()
