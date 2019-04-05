"""
Model to define a Language
"""

from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone


class Language(models.Model):
    """
    Class to define language database objects

    Args:
        models : Databas model inherit from the standard django models
    """

    DIRECTION = (
        ('ltr', 'left-to-right'),
        ('rtl', 'right-to-left')
    )

    # We use bcp47 language codes (see https://tools.ietf.org/html/bcp47).
    # The recommended minimum buffer is 35 (see https://tools.ietf.org/html/bcp47#section-4.4.1).
    # It's unlikely that we have language codes longer than 8 characters though.
    code = models.CharField(max_length=8, primary_key=True, validators=[MinLengthValidator(2)])
    title = models.CharField(max_length=250, blank=False)
    text_direction = models.CharField(default=DIRECTION[0][0], choices=DIRECTION, max_length=3)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
