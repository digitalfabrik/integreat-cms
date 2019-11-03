"""
Database model representing an autonomous authority
"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.http import Http404
from django.utils import timezone

from ..constants import region_status


class Region(models.Model):
    """
    Class to generate region database objects
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True, allow_unicode=True)
    status = models.CharField(max_length=8, choices=region_status.CHOICES, default=region_status.HIDDEN)

    events_enabled = models.BooleanField(default=True)
    push_notifications_enabled = models.BooleanField(default=True)
    push_notification_channels = ArrayField(models.CharField(max_length=60), blank=True)

    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    postal_code = models.CharField(max_length=10)

    admin_mail = models.EmailField()

    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    statistics_enabled = models.BooleanField(default=False)
    matomo_url = models.CharField(max_length=150, blank=True, default='')
    matomo_token = models.CharField(max_length=150, blank=True, default='')
    matomo_ssl_verify = models.BooleanField(default=True)

    @property
    def languages(self):
        language_tree_nodes = self.language_tree_nodes.select_related('language').all()
        return [language_tree_node.language for language_tree_node in language_tree_nodes]

    @property
    def default_language(self):
        tree_root = self.language_tree_nodes.filter(level=0).first()
        return tree_root.language if tree_root else None

    @classmethod
    def get_current_region(cls, request):
        # if rendered url is edit_region, the region slug originates from the region form.
        if not hasattr(request, 'resolver_match') or request.resolver_match.url_name == 'edit_region':
            return None
        region_slug = request.resolver_match.kwargs.get('region_slug')
        if not region_slug:
            return None
        region = cls.objects.filter(slug=region_slug)
        if not region.exists():
            raise Http404
        return region.first()

    def __str__(self):
        """Function that provides a string representation of this object

        Returns: String
        """
        return self.name

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_regions', 'Can manage regions'),
        )
