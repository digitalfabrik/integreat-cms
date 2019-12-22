"""
Model to define a Language
"""
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Language(models.Model):
    """
    Class to define language database objects

    Args:
        models : Database model inherit from the standard django models
    """

    DIRECTION = (
        ('ltr', _('Left to right')),
        ('rtl', _('Right to left'))
    )

    # We use bcp47 language codes (see https://tools.ietf.org/html/bcp47).
    # The recommended minimum buffer is 35 (see https://tools.ietf.org/html/bcp47#section-4.4.1).
    # It's unlikely that we have language codes longer than 8 characters though.
    code = models.CharField(max_length=8, unique=True, validators=[MinLengthValidator(2)])
    native_name = models.CharField(max_length=250, blank=False)
    english_name = models.CharField(max_length=250, blank=False)
    text_direction = models.CharField(default=DIRECTION[0][0], choices=DIRECTION, max_length=3)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    # name of the language in the current backend language
    @property
    def translated_name(self):
        return _(self.english_name)

    def __str__(self):
        """Function that provides a string representation of this object

        Returns: String
        """
        return self.english_name

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_languages', 'Can manage languages'),
        )
