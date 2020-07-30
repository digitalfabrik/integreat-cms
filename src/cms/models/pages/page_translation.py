import logging

from django.conf import settings
from django.db import models
from django.utils import timezone

from .page import Page
from ..languages.language import Language
from ...constants import status


logger = logging.getLogger(__name__)


class PageTranslation(models.Model):
    """
    Data model representing a page translation

    :param id: The database id of the page translation
    :param slug: The slug identifier of the translation (unique per :class:`~cms.models.regions.region.Region` and
                 :class:`~cms.models.languages.language.Language`)
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

    page = models.ForeignKey(
        Page, related_name="translations", on_delete=models.CASCADE
    )
    language = models.ForeignKey(
        Language, related_name="page_translations", on_delete=models.CASCADE
    )
    slug = models.SlugField(max_length=200, blank=True, allow_unicode=True)
    title = models.CharField(max_length=250)
    text = models.TextField(blank=True)
    status = models.CharField(
        max_length=6, choices=status.CHOICES, default=status.DRAFT
    )
    currently_in_translation = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="page_translations",
        null=True,
        on_delete=models.SET_NULL,
    )
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def foreign_object(self):
        """
        This property is an alias of the page foreign key and is needed to generalize the :mod:`~cms.utils.slug_utils`
        for all content types

        :return: The page to which the translation belongs
        :rtype: ~cms.models.pages.page.Page
        """
        return self.page

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
    def available_languages(self):
        """
        This property checks in which :class:`~cms.models.languages.language.Language` the page is translated apart
        from ``self.language``.
        It only returns languages which have a public translation, so drafts are not included here.
        The returned dict has the following format::

            {
                available_translation.language.code: {
                    'id': available_translation.id,
                    'url': available_translation.permalink
                },
                ...
            }

        :return: A dictionary containing the available languages of a page translation
        :rtype: dict
        """
        languages = self.page.languages
        languages.remove(self.language)
        available_languages = {}
        for language in languages:
            other_translation = self.page.get_public_translation(language.code)
            if other_translation:
                available_languages[language.code] = {
                    "id": other_translation.id,
                    "url": other_translation.permalink,
                }
        return available_languages

    @property
    def source_translation(self):
        """
        This property returns the translation which was used to create the ``self`` translation.
        It derives this information from the :class:`~cms.models.regions.region.Region`'s root
        :class:`~cms.models.languages.language_tree_node.LanguageTreeNode`.

        :return: The page translation in the source :class:`~cms.models.languages.language.Language` (:obj:`None` if
                 the translation is in the :class:`~cms.models.regions.region.Region`'s default
                 :class:`~cms.models.languages.language.Language`)
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        source_language_tree_node = self.page.region.language_tree_nodes.get(
            language=self.language
        ).parent
        if source_language_tree_node:
            return self.page.get_translation(source_language_tree_node.code)
        return None

    @property
    def latest_public_revision(self):
        """
        This property is a link to the most recent public version of this translation.
        If the translation itself is not public, this property can return a revision which is older than ``self``.

        :return: The latest public revision of the translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.page.translations.filter(
            language=self.language, status=status.PUBLIC,
        ).first()

    @property
    def latest_major_revision(self):
        """
        This property is a link to the most recent major version of this translation.

        :return: The latest major revision of the translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.page.translations.filter(
            language=self.language, minor_edit=False,
        ).first()

    @property
    def latest_major_public_revision(self):
        """
        This property is a link to the most recent major public version of this translation.
        This is used when translations, which are derived from this translation, check whether they are up to date.

        :return: The latest major public revision of the translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.page.translations.filter(
            language=self.language, status=status.PUBLIC, minor_edit=False,
        ).first()

    @property
    def previous_revision(self):
        """
        This property is a shortcut to the previous revision of this translation

        :return: The previous translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        version = self.version - 1
        return self.page.translations.filter(
            language=self.language, version=version,
        ).first()

    @property
    def is_outdated(self):
        """
        This property checks whether a translation is outdated and thus needs a new revision of the content.
        This happens, when the source translation is updated and the update is no `minor_edit`.

        * If the translation is currently being translated, it is considered not outdated.
        * If the translation's language is the region's default language, it is defined to be never outdated.
        * If the translation's source translation is already outdated, then the translation itself also is.
        * If neither the translation nor its source translation have a latest major public translation, it is defined as
          not outdated.
        * If neither the translation nor its source translation have a latest major public translation, it is defined as
          not outdated.

        Otherwise, the outdated flag is calculated by comparing the `last_updated`-field of the translation and its
        source translation.

        :return: Flag to indicate whether the translation is outdated
        :rtype: bool
        """
        # If the page translation is currently in translation, it is defined as not outdated
        if self.currently_in_translation:
            return False
        source_translation = self.source_translation
        # If self.language is the root language, this translation can never be outdated
        if not source_translation:
            return False
        # If the source translation is outdated, this translation can not be up to date
        if source_translation.is_outdated:
            return True
        self_revision = self.latest_major_public_revision
        source_revision = source_translation.latest_major_public_revision
        # If one of the translations has no major public revision, it cannot be outdated
        if not self_revision or not source_revision:
            return False
        return self_revision.last_updated < source_revision.last_updated

    @property
    def is_up_to_date(self):
        """
        This property checks whether a translation is up to date.
        A translation is considered up to date when it is not outdated and not being translated at the moment.

        :return: Flag which indicates whether a translation is up to date
        :rtype: bool
        """
        return not self.currently_in_translation and not self.is_outdated

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

        :param region_slug: The requested :class:`~cms.models.regions.region.Region`
        :type region_slug: ~cms.models.regions.region.Region

        :param language_code: The requested :class:`~cms.models.languages.language.Language`
        :type language_code: ~cms.models.languages.language.Language

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

        :param region_slug: The requested :class:`~cms.models.regions.region.Region`
        :type region_slug: ~cms.models.regions.region.Region

        :param language_code: The requested :class:`~cms.models.languages.language.Language`
        :type language_code: ~cms.models.languages.language.Language

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

        :param region_slug: The requested :class:`~cms.models.regions.region.Region`
        :type region_slug: ~cms.models.regions.region.Region

        :param language_code: The requested :class:`~cms.models.languages.language.Language`
        :type language_code: ~cms.models.languages.language.Language

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

        :param region_slug: The requested :class:`~cms.models.regions.region.Region`
        :type region_slug: ~cms.models.regions.region.Region

        :param language_code: The requested :class:`~cms.models.languages.language.Language`
        :type language_code: ~cms.models.languages.language.Language

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
        return super(PageTranslation, self).__str__()

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
