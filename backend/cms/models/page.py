from django.contrib.auth.models import User
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from cms.models.site import Site
from cms.models.language import Language


class Page(MPTTModel):
    order = models.IntegerField(default=0)
    parent = TreeForeignKey('self',
                            blank=True,
                            null=True,
                            related_name='children')
    icon = models.ImageField(blank=True,
                             null=True,
                             upload_to='pages/%Y/%m/%d')
    site = models.ForeignKey(Site)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        # TODO: get current language title
        pt = PageTranslation.objects.filter(
            page_id=self.id,
            language='de').first()
        return pt.title

    @classmethod
    def get_tree_view(cls):
        page_translations = PageTranslation.objects.filter(
            language='de'
        ).select_related('user')
        pages = cls.objects.all().prefetch_related(models.Prefetch(
            'page_translations',
            queryset=page_translations)).filter(page_translations__language='de')

        return pages

    def depth(self):
        return len(self.get_ancestors())


    class MPTTMeta:
        order_insertion_by = ['order']


class PageTranslation(models.Model):
    page = models.ForeignKey(Page, related_name='page_translations')
    permalink = models.CharField(max_length=60)
    STATUS = (
        ('draft', 'Entwurf'),
        ('in-review', 'Ausstehender Review'),
        ('reviewed', 'Review abgeschlossen'),
    )
    title = models.CharField(max_length=250)
    status = models.CharField(max_length=9, choices=STATUS, default='draft')
    text = models.TextField()
    language = models.ForeignKey(Language)
    version = models.PositiveIntegerField(default=0)
    public = models.BooleanField(default=False)
    minor_edit = models.BooleanField(default=False)
    creator = models.ForeignKey(User)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
