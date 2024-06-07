from __future__ import annotations

import logging
from html import escape
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property

if TYPE_CHECKING:
    from datetime import datetime

    from django.db.models.query import QuerySet
    from django.utils.functional import Promise
    from django.utils.safestring import SafeString

    from ..language.language import Language
    from ..regions.region import Region

from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link

from ..decorators import modify_fields
from .abstract_base_page_translation import AbstractBasePageTranslation

logger = logging.getLogger(__name__)


@modify_fields(
    slug={"verbose_name": _("page link")},
    title={"verbose_name": _("title of the page")},
    content={"verbose_name": _("content of the page")},
)
class PageTranslation(AbstractBasePageTranslation):
    """
    Data model representing a page translation
    """

    links = GenericRelation(Link, related_query_name="page_translation")

    page = models.ForeignKey(
        "cms.Page",
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("page"),
    )

    hix_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("HIX score"),
    )

    hix_feedback = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("HIX feedback"),
    )

    @cached_property
    def ancestor_path(self) -> str:
        """
        This property calculates the path of all parents of the page

        :return: The relative path to the page
        """
        slugs = []
        for ancestor in self.page.get_cached_ancestors():
            if public_translation := ancestor.get_public_translation(
                self.language.slug
            ):
                slugs.append(public_translation.slug)
                continue
            if translation := ancestor.get_translation(self.language.slug):
                slugs.append(translation.slug)
                continue
            slugs.append(ancestor.best_translation.slug)
        return "/".join(slugs)

    @cached_property
    def url_infix(self) -> str:
        """
        Generates the infix of the url of the page translation object which is the ancestor path of the page

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        :return: the infix of the url
        """
        return self.ancestor_path

    @cached_property
    def backend_edit_link(self) -> str:
        """
        This function returns the absolute url to the editor for this translation

        :return: The url
        """
        return reverse(
            "edit_page",
            kwargs={
                "page_id": self.page.id,
                "language_slug": self.language.slug,
                "region_slug": self.page.region.slug,
            },
        )

    @cached_property
    def short_url(self) -> str:
        """
        This function returns the absolute short url to the page translation

        :return: The short url of a page translation
        """

        return settings.SHORT_LINKS_URL + reverse(
            "public:expand_page_translation_id", kwargs={"short_url_id": self.id}
        )

    @cached_property
    def mirrored_translation_text(self) -> str:
        """
        This method returns the text of the mirrored translation or an empty string,
        if it is not available in this language

        :return: The text
        """
        if self.page.mirrored_page:
            if translation := self.page.get_mirrored_page_translation(
                self.language.slug
            ):
                return translation.content
        return ""

    @cached_property
    def mirrored_translation_text_or_fallback_message(self) -> str:
        """
        This method returns the text of the mirrored translation.
        If there is no mirrored translation, it returns an empty string.
        If there is a mirrored page but no translation, a html error message will be returned with languages that are translated as options.

        :return: The text, as specified
        """

        # If there is no page embetted
        if not self.page.mirrored_page:
            return ""

        # If the mirrored content is available in the current language
        if content := self.mirrored_translation_text:
            return content

        # Get all translations of this page which have a corresponding translation of the mirrored page
        languages = (
            self.page.mirrored_page.prefetched_major_public_translations_by_language_slug.keys()
        )
        translations = [
            self.page.get_public_translation(language_slug)
            for language_slug in languages
            if (
                translation := self.page.get_mirrored_page_translation(language_slug)
            ).content
            and len(translation.content)
        ]

        # If the mirrored content is available in no language
        if not translations:
            return ""

        # If a fall back exits
        error_message = (
            self.language.message_partial_live_content_not_available
            if self.content and not self.content.isspace()
            else self.language.message_content_not_available
        )

        return render_to_string(
            "pages/_page_content_alternatives.html",
            {"error_message": error_message, "translations": translations},
        )

    @cached_property
    def display_content(self) -> str:
        """
        This property returns the content that can be displayed to the user.
        This is just the normal content unless this translation is empty. Then a message will be returned
        which prompts the user to view the page in another language instead.

        :return: Html text for the content of this translation
        """
        if self.content and not self.content.isspace() or self.page.mirrored_page:
            return self.content

        fallback_translations = [
            translation
            for translation in self.page.prefetched_public_translations_by_language_slug.values()
            if translation.content
            and not translation.content.isspace()
            and translation.language in self.page.region.visible_languages
        ]

        if not fallback_translations:
            return self.content

        return render_to_string(
            "pages/_page_content_alternatives.html",
            {
                "error_message": self.language.message_content_not_available,
                "translations": fallback_translations,
            },
        )

    @cached_property
    def combined_text(self) -> str:
        """
        This function combines the text from this PageTranslation with the text from the mirrored page.
        Mirrored content always includes the live content from another page. This content needs to be added when
        delivering content to end users.
        If the mirrored page is not available in the current language, or if the content is empty,
        an error message for the user will be used instead.

        :return: The combined content of this page and the mirrored page
        """
        if self.page.mirrored_page_first:
            return (
                self.mirrored_translation_text_or_fallback_message
                + self.display_content
            )
        return self.display_content + self.mirrored_translation_text_or_fallback_message

    @cached_property
    def combined_last_updated(self) -> datetime:
        """
        This function combines the last_updated date from this PageTranslation and from a mirrored page.
        If this translation has no content, then the date from the mirrored translation will be used. In
        other cases, the date from this translation will be used.

        :return: The last_updated date of this or the mirrored page translation
        """
        mirrored_page_translation = self.page.get_mirrored_page_translation(
            self.language.slug
        )
        if (
            not self.content
            and mirrored_page_translation
            and mirrored_page_translation.content
        ):
            return mirrored_page_translation.last_updated
        return self.last_updated

    @cached_property
    def is_empty(self) -> bool:
        """
        This property returns whether the content of this translation is empty

        :return: Whether the content of this translation is empty
        """
        if self.content:
            return False

        # The translation is considered empty when its mirrored translation is empty or does not exist
        translation = self.page.get_mirrored_page_translation(self.language.slug)
        return not translation or not translation.content

    @cached_property
    def tags(self) -> list[Promise]:
        """
        This functions returns a list of translated tags which apply to this function.
        Supported tags:
        * Live content: if the page of this translation has live content
        * Empty: if the page contains no text and has no non-archived subpages

        :return: A list of tags which apply to this translation
        """
        tags = []

        if self.page.mirrored_page:
            tags.append(_("Live content"))

        if self.is_empty and (
            self.page.is_leaf()
            or not self.page.children.filter(explicitly_archived=False).exists()
        ):
            tags.append(_("Empty"))

        return tags

    @classmethod
    def get_translations(
        cls, region: Region, language: Language
    ) -> QuerySet[PageTranslation]:
        """
        This function retrieves the most recent versions of a all :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation`
        objects of a :class:`~integreat_cms.cms.models.regions.region.Region` in a specific :class:`~integreat_cms.cms.models.languages.language.Language`

        :param region: The requested :class:`~integreat_cms.cms.models.regions.region.Region`
        :param language: The requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: A :class:`~django.db.models.query.QuerySet` of all page translations of a region in a specific language
        """
        return cls.objects.filter(page__region=region, language=language).distinct(
            "page"
        )

    @classmethod
    def get_up_to_date_translations(
        cls, region: Region, language: Language
    ) -> QuerySet[PageTranslation]:
        """
        This function is similar to :func:`~integreat_cms.cms.models.pages.page_translation.PageTranslation.get_translations` but
        returns only page translations which are up to date

        :param region: The requested :class:`~integreat_cms.cms.models.regions.region.Region`
        :param language: The requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: All up to date translations of a region in a specific language
        """
        return [
            t
            for t in cls.objects.filter(
                page__region=region, language=language
            ).distinct("page")
            if t.is_up_to_date
        ]

    @classmethod
    def get_current_translations(
        cls, region: Region, language: Language
    ) -> QuerySet[PageTranslation]:
        """
        This function is similar to :func:`~integreat_cms.cms.models.pages.page_translation.PageTranslation.get_translations` but
        returns only page translations which are currently being translated by an external translator

        :param region: The requested :class:`~integreat_cms.cms.models.regions.region.Region`
        :param language: The requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: All currently translated translations of a region in a specific language
        """
        return [
            t
            for t in cls.objects.filter(
                page__region=region, language=language
            ).distinct("page")
            if t.currently_in_translation
        ]

    @classmethod
    def get_outdated_translations(
        cls, region: Region, language: Language
    ) -> QuerySet[PageTranslation]:
        """
        This function is similar to :func:`~integreat_cms.cms.models.pages.page_translation.PageTranslation.get_translations` but
        returns only page translations which are outdated

        :param region: The requested :class:`~integreat_cms.cms.models.regions.region.Region`
        :param language: The requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: All outdated translations of a region in a specific language
        """
        return [
            t
            for t in cls.objects.filter(
                page__region=region, language=language
            ).distinct("page")
            if t.is_outdated
        ]

    def path(self) -> SafeString:
        """
        This method returns a human-readable path that should uniquely identify this page translation within a given region

        :return: The path
        """
        label = " → ".join(
            [
                # escape page title because string is marked as safe afterwards
                escape(
                    (
                        ancestor.prefetched_public_translations_by_language_slug.get(
                            self.language.slug
                        )
                        or ancestor.best_translation
                    ).title
                )
                for ancestor in self.page.get_cached_ancestors(include_self=True)
            ]
        )
        # Add warning if page is archived
        if self.page.archived:
            label += " (⚠ " + _("Archived") + ")"
        # mark as safe so that the arrow and the warning triangle are not escaped
        return mark_safe(label)

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("page translations")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "page_translations"
        #: The default permissions for this model
        default_permissions = ()
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["page__pk", "language__pk", "-version"]
        #: A list of database constraints for this model
        constraints = [
            models.UniqueConstraint(
                fields=["page", "language", "version"],
                name="%(class)s_unique_version",
            ),
        ]
