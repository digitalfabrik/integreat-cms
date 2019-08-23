"""
Integreat extras are extended features beyond pages and
events that are usually provided by foreign services.
"""
from django.db import models
from django.utils import timezone

from .region import Region
from .extra_template import ExtraTemplate


class Extra(models.Model):
    """
    An extra (addon) is activated per region. For each extra,
    a template exists which can be used during activation.
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    template = models.ForeignKey(ExtraTemplate, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    # pylint: disable=C0111
    def alias(self):
        # pylint: disable=E1101
        return self.template.alias

    # pylint: disable=C0111
    def name(self):
        return self.template.name

    # pylint: disable=C0111
    def thumbnail(self):
        # pylint: disable=E1101
        return self.template.thumbnail

    # pylint: disable=C0111
    def url(self):
        # pylint: disable=E1101
        return self.template.url

    # pylint: disable=C0111
    def post_data(self):
        # pylint: disable=E1101
        return self.template.post_data

    # pylint: disable=R0903
    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_extras', 'Can manage extras'),
        )
