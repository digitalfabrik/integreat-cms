"""
Form for creating a region object
"""

from django import forms
from django.utils.text import slugify
from ...models.site import Site


class RegionForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """
    push_notification_channels = forms.CharField(required=False)

    class Meta:
        model = Site
        fields = ['name', 'events_enabled', 'push_notifications_enabled',
                  'latitude', 'longitude', 'postal_code', 'admin_mail', 'statistics_enabled',
                  'matomo_url', 'matomo_token', 'matomo_ssl_verify', 'status']

    def __init__(self, *args, **kwargs):
        super(RegionForm, self).__init__(*args, **kwargs)

    def save_region(self, region_slug=None):
        """Function to create or update a region
            region_slug ([Integer], optional): Defaults to None. If it's not set creates
            a region or update the region with the given region slug.
        """

        slug = slugify(self.cleaned_data['name'])
        # if the slug has changed, make sure the slug derived from the name is unique
        if slug != region_slug and Site.objects.filter(slug=slug).exists():
            old_slug = slug
            i = 1
            while True:
                i += 1
                slug = old_slug + '-' + str(i)
                if not Site.objects.filter(slug=slug).exists():
                    break

        if region_slug:
            # save region
            region = Site.objects.get(slug=region_slug)
            region.slug = slug
            region.name = self.cleaned_data['name']
            region.events_enabled = self.cleaned_data['events_enabled']
            region.push_notifications_enabled = self.cleaned_data['push_notifications_enabled']
            region.latitude = self.cleaned_data['latitude']
            region.longitude = self.cleaned_data['longitude']
            region.postal_code = self.cleaned_data['postal_code']
            region.admin_mail = self.cleaned_data['admin_mail']
            region.statistics_enabled = self.cleaned_data['statistics_enabled']
            region.matomo_url = self.cleaned_data['matomo_url']
            region.matomo_token = self.cleaned_data['matomo_token']
            region.matomo_ssl_verify = self.cleaned_data['matomo_ssl_verify']
            region.status = self.cleaned_data['status']
            region.push_notification_channels = self.cleaned_data[
                'push_notification_channels'
            ].split(' ')
            region.save()
        else:
            # create region
            region = Site.objects.create(
                slug=slug,
                name=self.cleaned_data['name'],
                events_enabled=self.cleaned_data['events_enabled'],
                push_notifications_enabled=self.cleaned_data['push_notifications_enabled'],
                latitude=self.cleaned_data['latitude'],
                longitude=self.cleaned_data['longitude'],
                postal_code=self.cleaned_data['postal_code'],
                admin_mail=self.cleaned_data['admin_mail'],
                statistics_enabled=self.cleaned_data['statistics_enabled'],
                matomo_url=self.cleaned_data['matomo_url'],
                matomo_token=self.cleaned_data['matomo_token'],
                matomo_ssl_verify=self.cleaned_data['matomo_ssl_verify'],
                push_notification_channels=self.cleaned_data[
                    'push_notification_channels'
                ].split(' '),
                status=self.cleaned_data['status'],
            )
