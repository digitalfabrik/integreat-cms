"""Class defining event-related database models

Raises:
    ValidationError: Raised when an value does not match the requirements
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from .event import Event
from ..languages.language import Language
from ...constants import status


class EventTranslation(models.Model):
    """
    Database object representing an event translation
    """

    event = models.ForeignKey(Event, related_name='translations', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=200, blank=True, allow_unicode=True)
    status = models.CharField(max_length=6, choices=status.CHOICES, default=status.DRAFT)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    language = models.ForeignKey(
        Language,
        related_name='event_translations',
        on_delete=models.CASCADE
    )
    currently_in_translation = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def foreign_object(self):
        return self.event

    @property
    def permalink(self):
        return '/'.join([
            self.event.region.slug,
            self.language.code,
            'events',
            self.slug
        ])

    @property
    def available_languages(self):
        languages = self.event.languages
        languages.remove(self.language)
        available_languages = {}
        for language in languages:
            other_translation = self.event.get_public_translation(language.code)
            if other_translation:
                available_languages[language.code] = {
                    'id': other_translation.id,
                    'url': other_translation.permalink
                }
        return available_languages

    @property
    def source_translation(self):
        source_language_tree_node = self.event.region.language_tree_nodes.get(language=self.language).parent
        if source_language_tree_node:
            return self.event.get_translation(source_language_tree_node.code)
        return None

    @property
    def latest_public_revision(self):
        return self.event.translations.filter(
            language=self.language,
            status=status.PUBLIC,
        ).first()

    @property
    def latest_major_revision(self):
        return self.event.translations.filter(
            language=self.language,
            minor_edit=False,
        ).first()

    @property
    def latest_major_public_revision(self):
        return self.event.translations.filter(
            language=self.language,
            status=status.PUBLIC,
            minor_edit=False,
        ).first()

    @property
    def previous_revision(self):
        version = self.version - 1
        return self.event.translations.filter(
            language=self.language,
            version=version,
        ).first()

    @property
    def is_outdated(self):
        # If the event translation is currently in translation, it is defined as not outdated
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
        return not self.currently_in_translation and not self.is_outdated

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['event', '-version']
        default_permissions = ()
