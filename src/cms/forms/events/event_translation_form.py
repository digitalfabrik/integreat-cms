import logging

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from ..custom_model_form import CustomModelForm
from ...constants import status
from ...models import EventTranslation
from ...utils.slug_utils import generate_unique_slug_helper

logger = logging.getLogger(__name__)


class EventTranslationForm(CustomModelForm):
    """
    Form for creating and modifying event translation objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = EventTranslation
        #: The fields of the model which should be handled by this form
        fields = [
            "title",
            "slug",
            "description",
            "status",
            "minor_edit",
        ]

    # pylint: disable=too-many-arguments
    def __init__(
        self, data=None, instance=None, disabled=False, region=None, language=None
    ):

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
            elif "submit_review" in data:
                data.update({"status": status.REVIEW})
            elif "submit_public" in data:
                data.update({"status": status.PUBLIC})

        # Instantiate ModelForm
        super().__init__(data=data, instance=instance)

        # If form is disabled because the user has no permissions to edit the page, disable all form fields
        if disabled:
            for _, field in self.fields.items():
                field.disabled = True

    # pylint: disable=arguments-differ
    def save(self, event=None, user=None):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param event: The event of this form's event translation instance
        :type event: ~cms.models.events.event.Event

        :param user: The author of this form's event instance
        :type user: ~django.contrib.auth.models.User

        :return: The saved event object
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """

        # Disable instant commit on saving because missing information would cause error
        event_translation = super().save(commit=False)

        if not self.instance.id:
            # set initial values for new events
            event_translation.event = event
            event_translation.language = self.language
            event_translation.creator = user

        # Only create new version if content changed
        if not {"slug", "title", "description"}.isdisjoint(self.changed_data):
            event_translation.version = event_translation.version + 1
            event_translation.pk = None

        event_translation.save()
        return event_translation

    def clean_slug(self):
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        :rtype: str
        """
        unique_slug = generate_unique_slug_helper(self, "event")
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
