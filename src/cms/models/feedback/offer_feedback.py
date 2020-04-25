"""
Module for models storing feedback from front end users
"""
from django.db import models

from .feedback import Feedback
from ..offers.offer import Offer


class OfferFeedback(Feedback):
    """
    Feedback on offers (offer model)
    """
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()
