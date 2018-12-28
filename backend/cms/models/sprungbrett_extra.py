from django.db import models

from cms.models.extra import Extra


class SprungbrettExtra(Extra):
    sprungbrett_location_name = models.CharField(max_length=250)

    def alias(self):
        return 'sprungbrett'

    def name(self):
        return 'Sprungbrett'

    def thumbnail(self):
        return 'https://cms.integreat-app.de/wp-content/uploads/extra-thumbnails/sprungbrett.jpg'

    def url(self):
        return 'https://web.integreat-app.de/proxy/sprungbrett/app-search-internships?location=' \
               + self.sprungbrett_location_name

    def post_data(self):
        return None
