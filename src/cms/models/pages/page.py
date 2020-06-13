"""Models representing a page and page translation with content
"""
import logging

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language

from mptt.models import MPTTModel, TreeForeignKey

from ..regions.region import Region
from ...constants import status

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
    mirrored_page_first = models.BooleanField(default=True, null=True, blank=True)
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
        page_translations = self.translations.prefetch_related('language').all()
        languages = []
        for page_translation in page_translations:
            if page_translation.language not in languages:
                languages.append(page_translation.language)
        return languages

    def get_translation(self, language_code):
        return self.translations.filter(
            language__code=language_code
        ).first()

    # Helper function for page labels, second level paths etc. where the ancestor translation might not exist
    def get_first_translation(self, priority_language_codes=None):
        # Taking [] directly as default parameter would be dangerous because it is mutable
        if not priority_language_codes:
            priority_language_codes = []
        for language_code in priority_language_codes + ['en-us', 'de-de']:
            if self.translations.filter(language__code=language_code).exists():
                return self.translations.filter(language__code=language_code).first()
        return self.translations.first()

    def get_public_translation(self, language_code):
        return self.translations.filter(
            language__code=language_code,
            status=status.PUBLIC,
        ).first()

    def get_mirrored_text(self, language_code):
        """
        This content needs to be added when delivering content to end users
        """
        if self.mirrored_page:
            return self.mirrored_page.get_translation(language_code).text
        return None

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
        if self.id:
            first_translation = self.get_first_translation()
            if first_translation:
                return f'(id: {self.id}, slug: {first_translation.slug} ({first_translation.language.code}))'
            return f'(id: {self.id})'
        return super(Page, self).__str__()

    @classmethod
    def get_tree(cls, region_slug, archived=False):
        """Function for building up a Treeview of all pages

        Args:
            region_slug: slug of the region the page belongs to
            archived:  if true archived pages will be included

        Returns:
            [pages]: Array of pages connected with their relations
        """

        return cls.objects.all().prefetch_related(
            'translations'
        ).filter(
            region__slug=region_slug,
            archived=archived
        )

    def best_language_title(self):
        page_translation = self.translations.filter(language__code=get_language())
        if not page_translation:
            alt_code = self.region.default_language.code
            page_translation = self.translations.filter(language__code=alt_code)
        return page_translation.first().title

    class Meta:
        default_permissions = ()
        permissions = (
            ('view_pages', 'Can view pages'),
            ('edit_pages', 'Can edit pages'),
            ('publish_pages', 'Can publish pages'),
            ('grant_page_permissions', 'Can grant page permissions'),
        )
