"""
Module for models storing feedback from front end users
"""
from django.db import models

from .feedback import Feedback


class SearchResultFeedback(Feedback):
    """
    Feedback on (i.e. empty) search results
    """
    searchQuery = models.CharField(max_length=1000)

    class Meta:
        default_permissions = ()
