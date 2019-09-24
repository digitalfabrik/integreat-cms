"""
Form for creating a region object
"""

from django import forms

from ...models.region import Region
from ..utils.slug_utils import generate_unique_slug


class RegionForm(forms.ModelForm):

    class Meta:
        model = Region
        fields = [
            'name',
            'slug',
            'events_enabled',
            'push_notifications_enabled',
            'push_notification_channels',
            'latitude',
            'longitude',
            'postal_code',
            'admin_mail',
            'statistics_enabled',
            'matomo_url',
            'matomo_token',
            'matomo_ssl_verify',
            'status'
        ]

    def clean_slug(self):
        return generate_unique_slug(self)
