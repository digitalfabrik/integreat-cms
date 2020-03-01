"""Models representing a page and page translation with content
"""
import logging

from django.conf import settings
from django.db import models
from django.utils import timezone

from .page import Page
from ..languages.language import Language
from ...constants import status


logger = logging.getLogger(__name__)


class PageTranslation(models.Model):
    """Class defining a Translation of a Page

    Args:
        models : Class inherit of django-Models
    """

    page = models.ForeignKey(Page, related_name='translations', on_delete=models.CASCADE)
    language = models.ForeignKey(
        Language,
        related_name='page_translations',
        on_delete=models.CASCADE
    )
    slug = models.SlugField(max_length=200, blank=True, allow_unicode=True)
    title = models.CharField(max_length=250)
    text = models.TextField(blank=True)
    status = models.CharField(max_length=6, choices=status.CHOICES, default=status.DRAFT)
    currently_in_translation = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def foreign_object(self):
        return self.page

    @property
    def ancestor_path(self):
        return '/'.join([
            ancestor.get_first_translation([self.language.code]).slug
            for ancestor in self.page.get_ancestors()
        ])

    @property
    def permalink(self):
        return '/'.join(filter(None, [
            self.page.region.slug,
            self.language.code,
            self.ancestor_path,
            self.slug
        ]))

    @property
    def available_languages(self):
        languages = self.page.languages
        languages.remove(self.language)
        available_languages = {}
        for language in languages:
            other_translation = self.page.get_public_translation(language.code)
            if other_translation:
                available_languages[language.code] = {
                    'id': other_translation.id,
                    'url': other_translation.permalink
                }
        return available_languages

    @property
    def source_translation(self):
        source_language_tree_node = self.page.region.language_tree_nodes.get(language=self.language).parent
        if source_language_tree_node:
            return self.page.get_translation(source_language_tree_node.code)
        return None

    @property
    def latest_public_revision(self):
        return self.page.translations.filter(
            language=self.language,
            status=status.PUBLIC,
        ).first()

    @property
    def latest_major_revision(self):
        return self.page.translations.filter(
            language=self.language,
            minor_edit=False,
        ).first()

    @property
    def latest_major_public_revision(self):
        return self.page.translations.filter(
            language=self.language,
            status=status.PUBLIC,
            minor_edit=False,
        ).first()

    @property
    def previous_revision(self):
        version = self.version - 1
        return self.page.translations.filter(
            language=self.language,
            version=version,
        ).first()

    @property
    def is_outdated(self):
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
    def combined_text(self):
        """
        Combines the text from the PageTranslation with the text from the mirrored page.
        """
        if self.page.mirrored_page_first:
            return self.page.get_mirrored_text(self.language.code) + self.text
        return self.text + self.page.get_mirrored_text(self.language.code)

    @classmethod
    def get_translations(cls, region, language):
        return cls.objects.filter(page__region=region, language=language).distinct('page')

    @classmethod
    def get_outdated_translations(cls, region, language):
        return [t for t in cls.objects.filter(page__region=region, language=language).distinct('page') if t.is_outdated]

    @classmethod
    def get_up_to_date_translations(cls, region, language):
        return [t for t in cls.objects.filter(page__region=region, language=language).distinct('page') if not t.is_outdated]

    def __str__(self):
        if self.id:
            return '(id: {}, page_id: {}, lang: {}, version: {}, slug: {})'.format(self.id, self.page.id, self.language.code, self.version, self.slug)
        return super(PageTranslation, self).__str__()

    class Meta:
        ordering = ['page', '-version']
        default_permissions = ()
