from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ...constants import text_directions
from ...utils.translation_utils import ugettext_many_lazy as __


class Language(models.Model):
    """
    Data model representing a content language.
    """

    slug = models.SlugField(
        max_length=8,
        unique=True,
        validators=[MinLengthValidator(2)],
        verbose_name=_("Language Slug"),
        help_text=_(
            "Unique string identifier used in URLs without spaces and special characters."
        ),
    )
    #: The recommended minimum buffer for `bcp47 <https://tools.ietf.org/html/bcp47>`__ is 35.
    #: It's unlikely that we have language slugs longer than 8 characters though.
    #: See `RFC 5646 Section 4.4.1. <https://tools.ietf.org/html/bcp47#section-4.4.1>`__
    #: Registered tags: https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry
    bcp47_tag = models.SlugField(
        max_length=35,
        unique=True,
        validators=[MinLengthValidator(2)],
        verbose_name=_("BCP47 Tag"),
        help_text=__(
            _("Language identifier without spaces and special characters."),
            _(
                "This field usually contains a combination of subtags from the IANA Subtag Registry."
            ),
        ),
    )
    native_name = models.CharField(
        max_length=250, blank=False, verbose_name=_("native name")
    )
    english_name = models.CharField(
        max_length=250, blank=False, verbose_name=_("name in English")
    )
    #: Manage choices in :mod:`cms.constants.text_directions`
    text_direction = models.CharField(
        default=text_directions.LEFT_TO_RIGHT,
        choices=text_directions.CHOICES,
        max_length=13,
        verbose_name=_("text direction"),
    )
    created_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )
    table_of_contents = models.CharField(
        max_length=250,
        blank=False,
        verbose_name=_('"Table of contents" in this language'),
        help_text=__(
            _('The native name for "Table of contents" in this language.'),
            _("This is used in exported PDFs."),
        ),
    )

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
        #: The verbose name of the model
        verbose_name = _("language")
        #: The plural verbose name of the model
        verbose_name_plural = _("languages")
        #: The default permissions for this model
        default_permissions = ()
        #:  The custom permissions for this model
        permissions = (("manage_languages", "Can manage languages"),)
