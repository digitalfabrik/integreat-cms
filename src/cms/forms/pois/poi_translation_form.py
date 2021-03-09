import logging

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from ..custom_model_form import CustomModelForm
from ...constants import status
from ...models import POITranslation
from ...utils.slug_utils import generate_unique_slug_helper


logger = logging.getLogger(__name__)


class POITranslationForm(CustomModelForm):
    """
    Form for creating and modifying POI translation objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = POITranslation
        #: The fields of the model which should be handled by this form
        fields = [
            "title",
            "short_description",
            "status",
            "description",
            "slug",
            "minor_edit",
        ]

    # pylint: disable=too-many-arguments
    def __init__(self, data=None, instance=None, region=None, language=None):
        """
        Initialize POI translation form

        :param data: submitted POST data
        :type data: dict

        :param instance: This form's instance
        :type instance: ~cms.models.pois.poi_translation.POITranslation

        :param region: The region of this form's instance
        :type region: ~cms.models.regions.region.Region

        :param language: The language of this form's instance
        :type language: ~cms.models.languages.language.Language
        """

        self.region = region
        self.language = language

        # To set the status value through the submit button, we have to overwrite the field value for status.
        # We could also do this in the save() function, but this would mean that it is not recognized in changed_data.
        # Check if POST data was submitted
        if data:
            # Copy QueryDict because it is immutable
            data = data.copy()
            # Update the POST field with the status corresponding to the submitted button
            if "submit_draft" in data:
                data.update({"status": status.DRAFT})
            elif "submit_public" in data:
                data.update({"status": status.PUBLIC})

        super().__init__(data=data, instance=instance)

        # If form is disabled because the user has no permissions to edit the page, disable all form fields
        if instance and instance.poi.archived:
            for _, field in self.fields.items():
                field.disabled = True

    # pylint: disable=arguments-differ
    def save(self, poi=None, user=None):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param poi: The POI translation instance of this form
        :type poi: ~cms.models.pois.poi_translation.POITranslation

        :param user: The author of the POI translation instance
        :type user: ~django.contrib.auth.models.User

        :return: The saved POI translation object
        :rtype: ~cms.models.pois.poi_translation.POITranslation
        """

        poi_translation = super().save(commit=False)

        if not self.instance.id:
            # only update these values when poi translation is created
            poi_translation.poi = poi
            poi_translation.creator = user
            poi_translation.language = self.language

        # Only create new version if content changed
        if not {"slug", "title", "short_description", "description"}.isdisjoint(
            self.changed_data
        ):
            poi_translation.version = poi_translation.version + 1
            poi_translation.pk = None
        poi_translation.save()

        return poi_translation

    def clean_slug(self):
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        :rtype: str
        """
        unique_slug = generate_unique_slug_helper(self, "poi")
        self.data = self.data.copy()
        self.data["slug"] = unique_slug
        return unique_slug

    def clean_description(self):
        """
        Validate the description field (see :ref:`overriding-modelform-clean-method`)

        :raises ~django.core.exceptions.ValidationError: When a heading 1 (``<h1>``) is used in the description

        :return: The valid description
        :rtype: str
        """
        description = self.data["description"]

        if "<h1>" in description:
            raise ValidationError(
                _("Use of Heading 1 style not allowed."),
                code="no-heading-1",
            )

        return description
