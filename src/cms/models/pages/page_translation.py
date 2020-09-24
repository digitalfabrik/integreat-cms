import logging

from django.conf import settings
from django.db import models

from .abstract_base_page_translation import AbstractBasePageTranslation

from .page import Page
from ..languages.language import Language


logger = logging.getLogger(__name__)


class PageTranslation(AbstractBasePageTranslation):
    """
    Data model representing a page translation

    :param id: The database id of the page translation
    :param slug: The slug identifier of the translation (unique per :class:`~cms.models.regions.region.Region` and
                 :class:`~cms.models.languages.language.Language`)

    Fields inherited from the :class:`~cms.models.pages.abstract_base_page_translation.AbstractBasePageTranslation` model:

    :param status: The status of the page translation (choices: :mod:`cms.constants.status`)
    :param title: The title of the page translation
    :param text: The content of the page translation
    :param currently_in_translation: Flag to indicate a translation is being updated by an external translator
    :param version: The revision number of the page translation
    :param minor_edit: Flag to indicate whether the difference to the previous revision requires an update in other
                       languages
    :param created_date: The date and time when the page translation was created
    :param last_updated: The date and time when the page translation was last updated

    Relationship fields:

    :param page: The page the translation belongs to (related name: ``translations``)
    :param language: The language of the page translation (related name: ``page_translations``)
    :param creator: The user who created the page translation (related name: ``page_translations``)
    """

    slug = models.SlugField(max_length=200, blank=True, allow_unicode=True)
    page = models.ForeignKey(
        Page, related_name="translations", on_delete=models.CASCADE
    )
    language = models.ForeignKey(
        Language, related_name="page_translations", on_delete=models.CASCADE
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="page_translations",
        null=True,
        on_delete=models.SET_NULL,
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
                ancestor.get_first_translation([self.language.code]).slug
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
                    self.language.code,
                    self.ancestor_path,
                    self.slug,
                ],
            )
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
        attached_text = self.page.get_mirrored_text(self.language.code)
        if attached_text is None:
            return self.text
        if self.page.mirrored_page_first:
            return attached_text + self.text
        return self.text + attached_text

    @classmethod
    def get_translations(cls, region, language):
        """
        This function retrieves the most recent versions of a all :class:`~cms.models.pages.PageTranslation` objects of
        a :class:`~cms.models.regions.region.Region` in a specific :class:`~cms.models.languages.language.Language`

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
            return f"(id: {self.id}, page_id: {self.page.id}, lang: {self.language.code}, version: {self.version}, slug: {self.slug})"
        return super().__str__()

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param ordering: The fields which are used to sort the returned objects of a QuerySet
        :type ordering: list [ str ]

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple
        """

        ordering = ["page", "-version"]
        default_permissions = ()
