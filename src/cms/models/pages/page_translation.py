import logging

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from backend.settings import BASE_URL
from .abstract_base_page_translation import AbstractBasePageTranslation
from .page import Page
from ..languages.language import Language
from ...utils.translation_utils import ugettext_many_lazy as __


logger = logging.getLogger(__name__)


class PageTranslation(AbstractBasePageTranslation):
    """
    Data model representing a page translation
    """

    slug = models.SlugField(
        max_length=200,
        blank=True,
        allow_unicode=True,
        verbose_name=_("Page link"),
        help_text=__(
            _("String identifier without spaces and special characters."),
            _("Unique per region and language."),
            _("Leave blank to generate unique parameter from title."),
        ),
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("page"),
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="page_translations",
        verbose_name=_("language"),
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="page_translations",
        verbose_name=_("creator"),
    )

    @property
    def ancestor_path(self):
        """
        This property calculates the path of all parents of the page

        :return: The relative path to the page
        :rtype: str
        """
        return "/".join(
            [
                ancestor.get_translation(self.language.slug).slug
                if ancestor.get_translation(self.language.slug)
                else ancestor.default_translation.slug
                for ancestor in self.page.get_ancestors()
            ]
        )

    @property
    def permalink(self):
        """
        This property calculates the permalink dynamically by joining the parent path together with the slug

        :return: The permalink of the page
        :rtype: str
        """
        return "/".join(
            filter(
                None,
                [
                    self.page.region.slug,
                    self.language.slug,
                    self.ancestor_path,
                    self.slug,
                ],
            )
        )

    @property
    def short_url(self):
        """
        This function returns the absolute short url to the page translation

        :return: The short url of a page translation
        :rtype: str
        """

        return BASE_URL + reverse(
            "expand_page_translation_id", kwargs={"short_url_id": self.id}
        )

    @property
    def combined_text(self):
        """
        This function combines the text from this PageTranslation with the text from the mirrored page.
        Mirrored content always includes the live content from another page. This content needs to be added when
        delivering content to end users.

        :return: The combined content of this page and the mirrored page
        :rtype: str
        """
        mirrored_page_translation = self.page.get_mirrored_page_translation(
            self.language.slug
        )
        if not mirrored_page_translation or not mirrored_page_translation.text:
            return self.text
        if self.page.mirrored_page_first:
            return mirrored_page_translation.text + self.text
        return self.text + mirrored_page_translation.text

    @property
    def combined_last_updated(self):
        """
        This function combines the last_updated date from this PageTranslation and from a mirrored page.
        If this translation has no content, then the date from the mirrored translation will be used. In
        other cases, the date from this translation will be used.

        :return: The last_updated date of this or the mirrored page translation
        :rtype: ~datetime.datetime
        """
        mirrored_page_translation = self.page.get_mirrored_page_translation(
            self.language.slug
        )
        if (
            not self.text
            and mirrored_page_translation
            and mirrored_page_translation.text
        ):
            return mirrored_page_translation.last_updated
        return self.last_updated

    @classmethod
    def get_translations(cls, region, language):
        """
        This function retrieves the most recent versions of a all :class:`~cms.models.pages.page_translation.PageTranslation`
        objects of a :class:`~cms.models.regions.region.Region` in a specific :class:`~cms.models.languages.language.Language`

        :param region: The requested :class:`~cms.models.regions.region.Region`
        :type region: ~cms.models.regions.region.Region

        :param language: The requested :class:`~cms.models.languages.language.Language`
        :type language: ~cms.models.languages.language.Language

        :return: A :class:`~django.db.models.query.QuerySet` of all page translations of a region in a specific language
        :rtype: ~django.db.models.query.QuerySet
        """
        return cls.objects.filter(page__region=region, language=language).distinct(
            "page"
        )

    @classmethod
    def get_up_to_date_translations(cls, region, language):
        """
        This function is similar to :func:`~cms.models.pages.page_translation.PageTranslation.get_translations` but
        returns only page translations which are up to date

        :param region: The requested :class:`~cms.models.regions.region.Region`
        :type region: ~cms.models.regions.region.Region

        :param language: The requested :class:`~cms.models.languages.language.Language`
        :type language: ~cms.models.languages.language.Language

        :return: All up to date translations of a region in a specific language
        :rtype: list [ ~cms.models.pages.page_translation.PageTranslation ]
        """
        return [
            t
            for t in cls.objects.filter(
                page__region=region, language=language
            ).distinct("page")
            if t.is_up_to_date
        ]

    @classmethod
    def get_current_translations(cls, region, language):
        """
        This function is similar to :func:`~cms.models.pages.page_translation.PageTranslation.get_translations` but
        returns only page translations which are currently being translated by an external translator

        :param region: The requested :class:`~cms.models.regions.region.Region`
        :type region: ~cms.models.regions.region.Region

        :param language: The requested :class:`~cms.models.languages.language.Language`
        :type language: ~cms.models.languages.language.Language

        :return: All currently translated translations of a region in a specific language
        :rtype: list [ ~cms.models.pages.page_translation.PageTranslation ]
        """
        return [
            t
            for t in cls.objects.filter(
                page__region=region, language=language
            ).distinct("page")
            if t.currently_in_translation
        ]

    @classmethod
    def get_outdated_translations(cls, region, language):
        """
        This function is similar to :func:`~cms.models.pages.page_translation.PageTranslation.get_translations` but
        returns only page translations which are outdated

        :param region: The requested :class:`~cms.models.regions.region.Region`
        :type region: ~cms.models.regions.region.Region

        :param language: The requested :class:`~cms.models.languages.language.Language`
        :type language: ~cms.models.languages.language.Language

        :return: All outdated translations of a region in a specific language
        :rtype: list [ ~cms.models.pages.page_translation.PageTranslation ]
        """
        return [
            t
            for t in cls.objects.filter(
                page__region=region, language=language
            ).distinct("page")
            if t.is_outdated
        ]

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <PageTranslation object at 0xDEADBEEF>

        :return: The string representation of the page translation with information about the most important fields
                 (useful for debugging purposes)
        :rtype: str
        """
        if self.id:
            return f"(id: {self.id}, page_id: {self.page.id}, lang: {self.language.slug}, version: {self.version}, slug: {self.slug})"
        return super().__str__()

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("page translations")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["page", "-version"]
        #: The default permissions for this model
        default_permissions = ()
