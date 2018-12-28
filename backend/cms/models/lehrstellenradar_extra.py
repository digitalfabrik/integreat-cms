from cms.models.extra import Extra


class LehrstellenradarExtra(Extra):

    def alias(self):
        return 'lehrstellen-radar'

    def name(self):
        return 'Lehrstellenradar'

    def thumbnail(self):
        return 'https://cms.integreat-app.de/wp-content/uploads/extra-thumbnails/lehrstellen' \
               '-radar.jpg'

    def url(self):
        return 'https://www.lehrstellen-radar.de/5100,0,lsrlist.html'

    def post_data(self):
        return {
            'search-ls': '1',
            'search-plz': self.site.postal_code,
            'search-pr': '1',
            'search-radius': '50'
        }
