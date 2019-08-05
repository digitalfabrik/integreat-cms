"""Models representing a page and page translation with content
"""

import logging

from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
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
            languages.append(page_translation.language)
        return languages

    def get_translation(self, language_code):
        try:
            page_translation = self.page_translations.get(language__code=language_code)
        except ObjectDoesNotExist:
            page_translation = None
        return page_translation

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

    page = models.ForeignKey(Page, related_name='page_translations', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=200, blank=True)
    STATUS = (
        ('draft', _('Draft')),
        ('in-review', _('Pending Review')),
        ('reviewed', _('Finished Review')),
    )
    title = models.CharField(max_length=250)
    status = models.CharField(max_length=9, choices=STATUS, default='draft')
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

    def __str__(self):
        return '(id: {}, slug: {})'.format(self.id, self.slug)

    class Meta:
        default_permissions = ()
