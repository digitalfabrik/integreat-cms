"""
Module for models storing feedback from front end users
"""
from django.db import models


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
    is_technical = models.BooleanField()
    read_status = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()
        permissions = (
            ('view_feedback', 'Can view feedback'),
        )
