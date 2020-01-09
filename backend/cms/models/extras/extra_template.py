"""Model to represent an Extra
"""
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone

from ...constants import postal_code


class ExtraTemplate(models.Model):
    """Model class for representing an Extra database object

    Args:
        models : Databas model inherit from the standard django models
    """

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    thumbnail = models.URLField(max_length=250)
    url = models.URLField(max_length=250)
    post_data = JSONField(max_length=250, default=dict, blank=True)
    use_postal_code = models.CharField(max_length=4, choices=postal_code.CHOICES, default=postal_code.NONE)

    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Function that provides a string representation of this object

        Returns: String
        """
        return self.name

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_extra_templates', 'Can manage extra templates'),
        )
