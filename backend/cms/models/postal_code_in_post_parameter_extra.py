from cms.models.extra import Extra


class PostalCodeInPostParameterExtra(Extra):

    def post_data(self):
        post = self.template.post_data
        post.update({'search-plz': self.site.postal_code})
        return post

    class Meta:
        default_permissions = ()
