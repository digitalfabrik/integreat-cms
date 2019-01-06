from cms.models.extra import Extra


class PostalCodeExtra(Extra):

    def url(self):
        return self.template.url + self.site.postal_code
