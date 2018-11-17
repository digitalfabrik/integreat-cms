from django.db import models
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey


class Page(MPTTModel):
    order = models.IntegerField(default=0)
    parent = TreeForeignKey('self',
                            blank=True,
                            null=True,
                            related_name='children')
    icon = models.ImageField(blank=True,
                             null=True,
                             upload_to='pages/%Y/%m/%d')
    pub_date = models.DateTimeField(auto_now_add=True)
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
            queryset=page_translations)
        ).filter(page_translations__language='de')

        return pages

    def depth(self):
        return len(self.get_ancestors())

    class MPTTMeta:
        order_insertion_by = ['order']


class PageTranslation(models.Model):
    STATUS = (
        ('draft', 'Entwurf'),
        ('review', 'Ausstehender Review'),
        ('public', 'Veröffentlicht'),
    )
    status = models.CharField(max_length=10, choices=STATUS, default='draft')
    title = models.CharField(max_length=250)
    text = models.TextField()
    permalink = models.CharField(max_length=60)
    language = models.CharField(max_length=2)
    version = models.PositiveIntegerField(default=0)
    active_version = models.BooleanField(default=False)
    page = models.ForeignKey(Page, related_name='page_translations')
    pub_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
