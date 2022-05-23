import logging

from ...constants import status
from ...models import EventTranslation
from ...utils.slug_utils import generate_unique_slug_helper
from ..custom_content_model_form import CustomContentModelForm

logger = logging.getLogger(__name__)


class EventTranslationForm(CustomContentModelForm):
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
            "content",
            "status",
            "minor_edit",
        ]

    def __init__(self, **kwargs):
        r"""
        Initialize event translation form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        # To set the status value through the submit button, we have to overwrite the field value for status.
        # We could also do this in the save() function, but this would mean that it is not recognized in changed_data.
        # Check if POST data was submitted
        if "data" in kwargs:
            # Copy QueryDict because it is immutable
            data = kwargs.pop("data").copy()
            # Update the POST field with the status corresponding to the submitted button
            if "submit_auto" in data:
                data["status"] = status.AUTO_SAVE
            elif "submit_draft" in data:
                data["status"] = status.DRAFT
            elif "submit_review" in data:
                data["status"] = status.REVIEW
            elif "submit_public" in data:
                data["status"] = status.PUBLIC
            # Set the kwargs to updated POST data again
            kwargs["data"] = data
            logger.debug(
                "Changed POST data 'status' manually to %r", data.get("status")
            )

        # Instantiate CustomModelForm
        super().__init__(**kwargs)

        # The slug is not required because it will be auto-generated if left blank
        self.fields["slug"].required = False

    # pylint: disable=arguments-differ
    def save(self, commit=True):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :type commit: bool

        :return: The saved event object
        :rtype: ~integreat_cms.cms.models.events.event_translation.EventTranslation
        """

        # Create new version if content changed
        if not {"slug", "title", "content"}.isdisjoint(self.changed_data):
            # Delete now outdated link objects
            self.instance.links.all().delete()
            # Save new version
            self.instance.version += 1
            self.instance.pk = None

        # Save CustomModelForm
        return super().save(commit=commit)

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
