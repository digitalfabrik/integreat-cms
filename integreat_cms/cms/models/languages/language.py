from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

from cacheops import invalidate_obj

from ..abstract_base_model import AbstractBaseModel
from ...constants import countries, text_directions
from ...utils.translation_utils import ugettext_many_lazy as __


class Language(AbstractBaseModel):
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
        max_length=250,
        blank=False,
        verbose_name=_("native name"),
        help_text=_("The name of the language in this language."),
    )
    english_name = models.CharField(
        max_length=250,
        blank=False,
        verbose_name=_("name in English"),
        help_text=_("The name of the language in English."),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.text_directions`
    text_direction = models.CharField(
        default=text_directions.LEFT_TO_RIGHT,
        choices=text_directions.CHOICES,
        max_length=13,
        verbose_name=_("text direction"),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.countries`
    primary_country_code = models.CharField(
        choices=countries.CHOICES,
        max_length=2,
        verbose_name=_("primary country flag"),
        help_text=__(
            _("The country with which this language is mainly associated."),
            _("This flag is used to represent the language graphically."),
        ),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.countries`
    secondary_country_code = models.CharField(
        choices=countries.CHOICES,
        blank=True,
        max_length=2,
        verbose_name=_("secondary country flag"),
        help_text=__(
            _("Another country with which this language is also associated."),
            _("This flag is used in the language switcher."),
        ),
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
    message_content_not_available = models.CharField(
        max_length=250,
        blank=False,
        default="This page does not exist in the selected language. It is however available in these languages:",
        verbose_name=_(
            '"This page does not exist in the selected language. It is however available in these languages:" in this language'
        ),
        help_text=_(
            "This is shown to the user when a page is not available in their language."
        ),
    )
    message_partial_live_content_not_available = models.CharField(
        max_length=250,
        blank=False,
        default="Part of the page does not exist in the selected language. It is however available in these languages:",
        verbose_name=_(
            '"Part of the page does not exist in the selected language. It is however available in these languages:" in this language'
        ),
        help_text=_(
            "This is shown to the user when the mirrored part of a page is not available in their language."
        ),
    )

    @cached_property
    def translated_name(self):
        """
        Returns the name of the language in the current backend language

        :return: The translated name of the language
        :rtype: str
        """
        return ugettext(self.english_name)

    def save(self, *args, **kwargs):
        r"""
        This overwrites the default Django :meth:`~django.db.models.Model.save` method,
        to invalidate the cache of the related objects.

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied kwargs
        :type \**kwargs: dict
        """
        super().save(*args, **kwargs)
        # Invalidate related objects
        for obj in self.language_tree_nodes.all():
            invalidate_obj(obj)
        for obj in self.page_translations.all():
            invalidate_obj(obj)
        for obj in self.event_translations.all():
            invalidate_obj(obj)
        for obj in self.poi_translations.all():
            invalidate_obj(obj)
        for obj in self.push_notification_translations.all():
            invalidate_obj(obj)

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Language object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the language
        :rtype: str
        """
        return self.translated_name

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Language: Language object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the language
        :rtype: str
        """
        return (
            f"<Language (id: {self.id}, slug: {self.slug}, name: {self.english_name})>"
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("language")
        #: The plural verbose name of the model
        verbose_name_plural = _("languages")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["bcp47_tag"]
