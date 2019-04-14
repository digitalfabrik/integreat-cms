"""
Database model representing an autonomous authority
"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Site(models.Model):
    """
    Class to generate site database objects
    """
    ACTIVE = 'acti'
    HIDDEN = 'hidd'
    ARCHIVED = 'arch'

    STATUS = (
        (ACTIVE, _('Active')),
        (HIDDEN, _('Hidden')),
        (ARCHIVED, _('Archived')),
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    status = models.CharField(max_length=4, choices=STATUS)

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

    @classmethod
    def get_current_site(cls, request):
        if hasattr(request, 'resolver_match'):
            site_slug = request.resolver_match.kwargs.get('site_slug')
            if site_slug:
                site = cls.objects.get(slug=site_slug)
                return site
        return None

    def __str__(self):
        return self.name
