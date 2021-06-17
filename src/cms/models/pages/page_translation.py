import logging

from html import escape

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from linkcheck.models import Link
from backend.settings import BASE_URL, WEBAPP_URL

from .abstract_base_page_translation import AbstractBasePageTranslation
from .page import Page
from ..languages.language import Language
from ...utils.translation_utils import ugettext_many_lazy as __


logger = logging.getLogger(__name__)


class PageTranslation(AbstractBasePageTranslation):
    """
    Data model representing a page translation
    """

    title = models.CharField(
        max_length=1024,
        verbose_name=_("title of the page"),
    )
    slug = models.SlugField(
        max_length=1024,
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
    text = models.TextField(
        blank=True,
        verbose_name=_("content of the page"),
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="page_translations",
        verbose_name=_("creator"),
    )
    links = GenericRelation(Link, related_query_name="page_translations")

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
    def base_link(self):
        """
        This property calculates the absolute page link without the slug dynamically

        :return: The base link of the page
        :rtype: str
        """
        return (
            "/".join(
                filter(
                    None,
                    [
                        WEBAPP_URL,
                        self.page.region.slug,
                        self.language.slug,
                        self.ancestor_path,
                    ],
                )
            )
            + "/"
        )

    @property
    def backend_base_link(self):
        """
        This property calculates the absolute page link on the CMS domain

        :return: The base link of the page
        :rtype: str
        """
        return (
            "/".join(
                filter(
                    None,
                    [
                        BASE_URL,
                        self.page.region.slug,
                        self.language.slug,
                        self.ancestor_path,
                        self.slug,
                    ],
                )
            )
            + "/"
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

    @property
    def tags(self):
        """
        This functions returns a list of translated tags which apply to this function.
        Supported tags:
        * Live content: if the page of this translation has live content
        * Empty: if the page contains no text

        :return: A list of tags which apply to this translation
        :rtype: list [ str ]
        """
        tags = []

        if self.page.mirrored_page:
            tags.append(_("Live content"))

        if not self.combined_text.strip():
            tags.append(_("Empty"))

        return tags

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

    @classmethod
    def search(cls, region, language_slug, query):
        """
        Searches for all page translations which match the given `query` in their title or slug.
        :param region: The current region
        :type region: ~cms.models.regions.region.Region
        :param language_slug: The language slug
        :type language_slug: str
        :param query: The query string used for filtering the pages
        :type query: str
        :return: A query for all matching objects
        :rtype: ~django.db.models.QuerySet
        """
        return (
            cls.objects.filter(
                **{
                    "page__region": region,
                    "language__slug": language_slug,
                }
            )
            .filter(Q(slug__icontains=query) | Q(title__icontains=query))
            .distinct("page")
        )

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``PageTranslation object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the page translation
        :rtype: str
        """
        label = " &rarr; ".join(
            [
                # escape page title because string is marked as safe afterwards
                escape(
                    ancestor.get_translation(self.language.slug).title
                    if ancestor.get_translation(self.language.slug)
                    else ancestor.best_translation.title
                )
                for ancestor in self.page.get_ancestors(include_self=True)
            ]
        )
        # Add warning if page is archived
        if self.page.archived:
            label += " (&#9888; " + _("Archived") + ")"
        # mark as safe so that the arrow and the warning triangle are not escaped
        return mark_safe(label)

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("page translations")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["page__pk", "-version"]
        #: The default permissions for this model
        default_permissions = ()
