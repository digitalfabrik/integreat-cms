from django.db import models
from django.utils import timezone

from .site import Site
from .extra_template import ExtraTemplate


class Extra(models.Model):
    site = models.ForeignKey(Site)
    template = models.ForeignKey(ExtraTemplate)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def alias(self):
        return self.template.alias

    def name(self):
        return self.template.name

    def thumbnail(self):
        return self.template.thumbnail

    def url(self):
        return self.template.url

    def post_data(self):
        return self.template.post_data

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_extras', 'Can manage extras'),
        )
