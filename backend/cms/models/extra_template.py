"""Model to represent an Extra
"""
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone


class ExtraTemplate(models.Model):
    """Model class for representing an Extra database object

    Args:
        models : Databas model inherit from the standard django models
    """

    name = models.CharField(max_length=250)
    alias = models.CharField(max_length=60)
    thumbnail = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    post_data = JSONField(max_length=250, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Function that provides a string representation of this object

        Returns: String
        """
        return self.name
