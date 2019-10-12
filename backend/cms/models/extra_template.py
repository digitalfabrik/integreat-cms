"""Model to represent an Extra
"""
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class ExtraTemplate(models.Model):
    """Model class for representing an Extra database object

    Args:
        models : Databas model inherit from the standard django models
    """
    POSTAL_NONE = 'POSTAL_NONE'
    POSTAL_GET = 'POSTAL_GET'
    POSTAL_POST = 'POSTAL_POST'

    POSTAL_CODE_CHOICES = (
        (POSTAL_NONE, _('No')),
        (POSTAL_GET, _('Append postal code to URL')),
        (POSTAL_POST, _('Add postal code to post parameters')),
    )

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    thumbnail = models.URLField(max_length=250)
    url = models.URLField(max_length=250)
    post_data = JSONField(max_length=250, default=dict, blank=True)
    use_postal_code = models.CharField(max_length=11, choices=POSTAL_CODE_CHOICES, default=POSTAL_NONE)

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
