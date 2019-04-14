"""Model representing a page with content
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from .language import Language
from .site import Site


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
    site = models.ForeignKey(Site, related_name='pages', on_delete=models.CASCADE)
    mirrored_page = models.ForeignKey('self', null=True, on_delete=models.PROTECT)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def depth(self):
        """Provide level of inheritance

        Returns:
            Int : Number of ancestors
        """

        return len(self.get_ancestors())

    def get_translation(self, language_code):
        language = Language.objects.get(code=language_code)
        return self.page_translations.get(language=language)

    def __str__(self):
        # TODO: get current language title
        translation = self.get_translation('de')
        if translation:
            return translation.title
        return ""

    @classmethod
    def get_tree_view(cls, request):
        """Function for building up a Treeview of all pages

        Returns:
            [pages]: Array of pages connected with their relations
        """

        page_translations = PageTranslation.objects.filter(
            language__code='de',
        ).select_related('creator')

        pages = cls.objects.all().prefetch_related(models.Prefetch(
            'page_translations',
            queryset=page_translations
        )).filter(
            page_translations__language__code='de',
            site__slug=Site.get_current_site(request).slug
        )
        return pages


class PageTranslation(models.Model):
    """Class defining a Translation of a Page

    Args:
        models : Class inherit of django-Models
    """

    page = models.ForeignKey(Page, related_name='page_translations', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=200, unique=True)
    STATUS = (
        ('draft', _('Draft')),
        ('in-review', _('Pending Review')),
        ('reviewed', _('Finished Review')),
    )
    title = models.CharField(max_length=250)
    status = models.CharField(max_length=9, choices=STATUS, default='draft')
    text = models.TextField()
    language = models.ForeignKey(Language, related_name='pages', on_delete=models.CASCADE)
    currently_in_translation = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=0)
    public = models.BooleanField(default=False)
    minor_edit = models.BooleanField(default=False)
    creator = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def permalink(self):
        permalink = self.page.site.slug + '/'
        permalink += self.language.code + '/'
        for ancestor in self.page.get_ancestors(include_self=True):
            permalink += ancestor.page_translations.get(language=self.language).slug + '/'
        return permalink

    def __str__(self):
        return self.title
