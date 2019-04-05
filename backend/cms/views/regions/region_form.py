"""
Form for creating a page object
"""

from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.text import slugify
from ...models.language import Language
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
        fields = ['name', 'languages', 'events_enabled', 'push_notifications_enabled',
                  'latitude', 'longitude', 'postal_code', 'admin_mail', 'statistics_enabled',
                  'matomo_url', 'matomo_token', 'matomo_ssl_verify', 'status']

    def __init__(self, *args, **kwargs):
        super(RegionForm, self).__init__(*args, **kwargs)
        self.fields["languages"].widget = CheckboxSelectMultiple()
        self.fields["languages"].queryset = Language.objects.all()

    def save_region(self, region_slug=None):
        """Function to create or update a page
            page_translation_id ([Integer], optional): Defaults to None. If it's not set creates
            a page or update the page with the given page id.
        """

        if region_slug:
            # save region
            region = Site.objects.get(slug=region_slug)
            region.name = self.cleaned_data['name']
            region.slug = slugify(self.cleaned_data['name'])
            region.languages = self.cleaned_data['languages']
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
                name=self.cleaned_data['name'],
                slug=slugify(self.cleaned_data['name']),
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
            region.languages = self.cleaned_data['languages']
            region.save()
