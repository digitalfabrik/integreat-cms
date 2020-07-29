
from django import forms

from ...models import OfferTemplate
from ...utils.slug_utils import generate_unique_slug


class OfferTemplateForm(forms.ModelForm):
    """
    Form for creating and modifying offer template objects
    """

    class Meta:
        model = OfferTemplate
        fields = [
            'name',
            'slug',
            'thumbnail',
            'url',
            'post_data',
            'use_postal_code'
        ]

    def __init__(self, *args, **kwargs):
        super(OfferTemplateForm, self).__init__(*args, **kwargs)

    def clean_slug(self):
        return generate_unique_slug(self, 'offer-template')

    def clean_post_data(self):
        cleaned_post_data = self.cleaned_data['post_data']
        if not cleaned_post_data:
            cleaned_post_data = dict()
        return cleaned_post_data
