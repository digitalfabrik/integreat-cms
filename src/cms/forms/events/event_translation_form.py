import logging

from django import forms

from ...constants import status
from ...models import EventTranslation
from ...utils.slug_utils import generate_unique_slug

logger = logging.getLogger(__name__)


class EventTranslationForm(forms.ModelForm):
    """
    Form for creating and modifying event translation objects
    """

    class Meta:
        model = EventTranslation
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
        logger.info(
            "EventTranslationForm instantiated with data %s and instance %s",
            data,
            instance,
        )

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
        logger.info(
            "EventTranslationForm saved with cleaned data %s and changed data %s",
            self.cleaned_data,
            self.changed_data,
        )

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
        unique_slug = generate_unique_slug(self, "event")
        self.data = self.data.copy()
        self.data["slug"] = unique_slug
        return unique_slug
