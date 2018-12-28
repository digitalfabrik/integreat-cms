from abc import abstractmethod

from django.db import models

from cms.models import Site


class Extra(models.Model):
    site = models.ForeignKey(Site)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    @abstractmethod
    def alias(self):
        pass

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def thumbnail(self):
        pass

    @abstractmethod
    def url(self):
        pass

    @abstractmethod
    def post_data(self):
        pass
