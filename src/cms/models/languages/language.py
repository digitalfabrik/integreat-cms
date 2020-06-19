from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ...constants import text_directions


class Language(models.Model):
    """
    Data model representing a content language.

    :param id: The database id of the language
    :param code: The bcp47 code of the language (see `RFC 5646 <https://tools.ietf.org/html/bcp47>`_). The recommended
                 minimum buffer is 35 (see `Section 4.4.1. <https://tools.ietf.org/html/bcp47#section-4.4.1>`_). It's
                 unlikely that we have language codes longer than 8 characters though.
    :param native_name: The native name of the language
    :param english_name: The name of the language in English
    :param text_direction: The text direction of the language (choices: :mod:`cms.constants.text_directions`)
    :param created_date: The date and time when the language was created
    :param last_updated: The date and time when the language was last updated

    Reverse relationships:

    :param language_tree_nodes: All language tree nodes of this language
    :param page_translations: All page translations in this language
    :param event_translations: All event translations in this language
    :param poi_translations: All poi translations in this language
    :param push_notification_translations: All push notification translations in this language
    """

    code = models.CharField(max_length=8, unique=True, validators=[MinLengthValidator(2)])
    native_name = models.CharField(max_length=250, blank=False)
    english_name = models.CharField(max_length=250, blank=False)
    text_direction = models.CharField(default=text_directions.LTR, choices=text_directions.CHOICES, max_length=3)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def translated_name(self):
        """
        Returns the name of the language in the current backend language

        :return: The translated name of the language
        :rtype: str
        """
        return _(self.english_name)

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <Language object at 0xDEADBEEF>

        :return: The string representation (in this case the English name) of the language
        :rtype: str
        """
        return self.english_name

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple

        :param permissions: The custom permissions for this model
        :type permissions: tuple
        """
        default_permissions = ()
        permissions = (
            ('manage_languages', 'Can manage languages'),
        )
