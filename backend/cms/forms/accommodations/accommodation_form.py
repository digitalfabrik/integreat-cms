"""
Form for creating a accommodation object and accommodation translation object
"""
import logging

from django import forms

from ...models import Accommodation, Language


logger = logging.getLogger(__name__)


class AccommodationForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = Accommodation
        fields = [
            'address',
            'postcode',
            'city',
            'country',
            'latitude',
            'longitude',
            'institution',
            'phone_number',
            'mobile_number',
            'wc_available',
            'shower_available',
            'animals_allowed',
            'intoxicated_allowed',
            'spoken_languages',
            'intake_from',
            'intake_to',
        ]
        widgets = {
            'spoken_languages': forms.CheckboxSelectMultiple(),
            'intake_from': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'intake_to': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }

    def __init__(self, data=None, instance=None, disabled=False):
        logger.info('AccommodationForm instantiated with data %s and instance %s', data, instance)

        # instantiate ModelForm
        super(AccommodationForm, self).__init__(data=data, instance=instance)

        self.fields['spoken_languages'].choices = [
            (language.id, language.translated_name) for language in Language.objects.all()
        ]

        # If form is disabled because the user has no permissions to edit the page, disable all form fields
        if disabled:
            for _, field in self.fields.items():
                field.disabled = True

    # pylint: disable=arguments-differ
    def save(self, region=None):
        logger.info('AccommodationForm saved with cleaned data %s and changed data %s', self.cleaned_data, self.changed_data)

        if self.instance.id:
            accommodation = super(AccommodationForm, self).save()
        else:
            accommodation = super(AccommodationForm, self).save(commit=False)
            # only update these values when accommodation is created
            accommodation.region = region
            accommodation.save()
            # many to many relationships can only be saved after the primary key exists
            accommodation.spoken_languages.set(self.cleaned_data['spoken_languages'])
            accommodation.save()

        return accommodation
