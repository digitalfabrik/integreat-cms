from django.db import models
from cms.models import Site
from cms.models.extra_template import ExtraTemplate


class Extra(models.Model):
    site = models.ForeignKey(Site)
    template = models.ForeignKey(ExtraTemplate)
    created_date = models.DateTimeField(auto_now_add=True)
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
