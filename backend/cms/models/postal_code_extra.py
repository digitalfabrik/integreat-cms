from cms.models.extra import Extra
from cms.models.extra_template import ExtraTemplate


class PostalCodeExtra(Extra):
    template = models.ForeignKey(ExtraTemplate)

    def alias(self):
        return self.template.alias

    def name(self):
        return self.template.name

    def thumbnail(self):
        return self.template.thumbnail

    def url(self):
        return self.template.url + self.site.postal_code

    def post_data(self):
        return self.template.post_data
