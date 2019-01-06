from cms.models.extra import Extra


class PostDataExtra(Extra):

    def post_data(self):
        return self.template.post_data.update({'search-plz': self.site.postal_code})
