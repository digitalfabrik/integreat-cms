"""
Module for models storing feedback from front end users
"""
from django.db import models

from .feedback import Feedback
from ..regions.region import Region


class RegionFeedback(Feedback):
    """
    General feedback for regions
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()
