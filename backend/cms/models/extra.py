"""
Integreat extras are extended features beyond pages and
events that are usually provided by foreign services.
"""
from django.db import models
from django.utils import timezone

from .region import Region
from .extra_template import ExtraTemplate
from ..constants import postal_code


class Extra(models.Model):
    """
    An extra (addon) is activated per region. For each extra,
    a template exists which can be used during activation.
    """
    region = models.ForeignKey(Region, related_name='extras', on_delete=models.CASCADE)
    template = models.ForeignKey(ExtraTemplate, related_name='extras', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def slug(self):
        return self.template.slug

    @property
    def name(self):
        return self.template.name

    @property
    def thumbnail(self):
        return self.template.thumbnail

    @property
    def url(self):
        if self.template.use_postal_code == postal_code.GET:
            return self.template.url + self.region.postal_code
        return self.template.url

    @property
    def post_data(self):
        post_data = self.template.post_data
        if self.template.use_postal_code == postal_code.POST:
            post_data.update({'search-plz': self.region.postal_code})
        return post_data

    class Meta:
        unique_together = (('region', 'template', ), )
        default_permissions = ()
        permissions = (
            ('manage_extras', 'Can manage extras'),
        )
