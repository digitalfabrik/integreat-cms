from django.db import models

from cms.models.extra import Extra
from cms.models.link_extra_template import LinkExtraTemplate


class SimpleLinkExtra(Extra):
    template = models.ForeignKey(LinkExtraTemplate)

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
