"""Models representing a page and page translation with content
"""

import logging

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey

from .language import Language
from .region import Region


logger = logging.getLogger(__name__)


class Page(MPTTModel):
    """Class that represents an Page database object

    Args:
        MPTTModel : Library for hierachical data structures
    """

    parent = TreeForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='children',
        on_delete=models.PROTECT
    )
    icon = models.ImageField(
        blank=True,
        null=True,
        upload_to='pages/%Y/%m/%d'
    )
    region = models.ForeignKey(Region, related_name='pages', on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)
    mirrored_page = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT)
    editors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='editors', blank=True)
    publishers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='publishers', blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def depth(self):
        """Provide level of inheritance

        Returns:
            Int : Number of ancestors
        """

        return len(self.get_ancestors())

    @property
    def languages(self):
        page_translations = self.page_translations.prefetch_related('language').all()
        languages = []
        for page_translation in page_translations:
            if page_translation.language not in languages:
                languages.append(page_translation.language)
        return languages

    def get_translation(self, language_code):
        return self.page_translations.filter(
            language__code=language_code
        ).first()

    def get_public_translation(self, language_code):
        return self.page_translations.filter(
            language__code=language_code,
            public=True,
            status=PageTranslation.REVIEW_FINISHED,
        ).first()

    def get_absolute_url(self):
        return reverse('edit_page', kwargs={
            'page_id': self.id,
            'region_slug': self.region.slug,
            'language_code': self.region.default_language.code,
        })

    @staticmethod
    def get_archived(region_slug):
        return Page.objects.filter(archived=True, region__slug=region_slug)

    @staticmethod
    def archived_count(region_slug):
        return Page.objects.filter(archived=True, region__slug=region_slug).count()

    def __str__(self):
        translations = PageTranslation.objects.filter(page=self)
        german_translation = translations.filter(language__code='de-de').first()
        english_translation = translations.filter(language__code='en-gb').first()
        if german_translation:
            slug = german_translation.slug
        elif english_translation:
            slug = english_translation.slug
        elif translations.exists():
            slug = translations.first()
        else:
            slug = ''
        return '(id: {}, slug: {})'.format(self.id, slug)

    @classmethod
    def get_tree(cls, region_slug, archived=False):
        """Function for building up a Treeview of all pages

        Args:
            region_slug: slug of the region the page belongs to
            archived:  if true archived pages will be included

        Returns:
            [pages]: Array of pages connected with their relations
        """

        if archived:
            pages = cls.objects.all().prefetch_related(
                'page_translations'
            ).filter(
                region__slug=region_slug
            )
        else:
            pages = cls.objects.all().prefetch_related(
                'page_translations'
            ).filter(
                region__slug=region_slug,
                archived=False
            )

        return pages

    class Meta:
        default_permissions = ()
        permissions = (
            ('view_pages', 'Can view pages'),
            ('edit_pages', 'Can edit pages'),
            ('publish_pages', 'Can publish pages'),
            ('grant_page_permissions', 'Can grant page permissions'),
        )


class PageTranslation(models.Model):
    """Class defining a Translation of a Page

    Args:
        models : Class inherit of django-Models
    """
    DRAFT = 'DRAFT'
    REVIEW_PENDING = 'PENDING'
    REVIEW_FINISHED = 'FINISHED'

    page = models.ForeignKey(Page, related_name='page_translations', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=200, blank=True)
    STATUS = (
        (DRAFT, _('Draft')),
        (REVIEW_PENDING, _('Pending Review')),
        (REVIEW_FINISHED, _('Finished Review')),
    )
    title = models.CharField(max_length=250)
    status = models.CharField(max_length=9, choices=STATUS, default=DRAFT)
    text = models.TextField()
    language = models.ForeignKey(
        Language,
        related_name='page_translations',
        on_delete=models.CASCADE
    )
    currently_in_translation = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=0)
    public = models.BooleanField(default=False)
    minor_edit = models.BooleanField(default=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def ancestor_path(self):
        return '/'.join([
            ancestor.page_translations.get(language=self.language).slug
            for ancestor in self.page.get_ancestors()
        ])

    @property
    def permalink(self):
        return '{}/{}/{}/{}'.format(
            self.page.region.slug, self.language.code, self.ancestor_path, self.slug
        )

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
        return self.page.page_translations.filter(
            language=self.language,
            public=True,
            status=self.REVIEW_FINISHED,
        ).first()

    @property
    def latest_major_revision(self):
        return self.page.page_translations.filter(
            language=self.language,
            minor_edit=False,
        ).first()

    @property
    def latest_major_public_revision(self):
        return self.page.page_translations.filter(
            language=self.language,
            public=True,
            status=self.REVIEW_FINISHED,
            minor_edit=False,
        ).first()

    @property
    def previous_revision(self):
        version = self.version - 1
        return self.page.page_translations.filter(
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
        # If on of the translations has no major public revision, it cannot be outdated
        if not self_revision or not source_revision:
            return False
        return self_revision.last_updated < source_revision.last_updated

    def __str__(self):
        return '(id: {}, slug: {})'.format(self.id, self.slug)

    class Meta:
        ordering = ['page', '-version']
        default_permissions = ()
