import logging
import mimetypes
from os.path import splitext

import magic

from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _

from ...constants import allowed_media
from ...models import MediaFile
from ...utils.media_utils import generate_thumbnail
from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class UploadMediaFileForm(CustomModelForm):
    """
    Form for uploading media file objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = MediaFile
        #: The fields of the model which should be handled by this form
        fields = (
            "file",
            "name",
            "type",
            "parent_directory",
            "thumbnail",
            "file_size",
            "last_modified",
        )

    def __init__(self, data=None, files=None, instance=None):
        """
        Initialize UploadMediaFileForm form

        :param data: submitted POST data
        :type data: dict

        :param data: A dictionary-like object containing all given HTTP POST parameters
        :type data: django.http.QueryDict

        :param files: A dictionary-like object containing all uploaded files
        :type files: django.utils.datastructures.MultiValueDict

        :param instance: This form's instance
        :type instance: ~integreat_cms.cms.models.media.media_file.MediaFile
        """

        # instantiate ModelForm
        super().__init__(data=data, files=files, instance=instance)

        # Make fields not required because they're filled automatically
        self.fields["name"].required = False
        self.fields["type"].required = False
        self.fields["thumbnail"].required = False
        self.fields["file_size"].required = False
        self.fields["last_modified"].required = False

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`:
        Don't allow multiple root nodes for one region:
        If the file type is invalid, add a :class:`~django.core.exceptions.ValidationError`.

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()

        file = cleaned_data.get("file")

        # Only validate type if a file is uploaded - otherwise, the form throws an error anyways
        if file:
            # Check magic bytes for actual file type - the content_type of the file can easily be forged
            cleaned_data["type"] = magic.from_buffer(file.read(), mime=True)
            if cleaned_data.get("type") not in dict(allowed_media.UPLOAD_CHOICES):
                self.add_error(
                    "type",
                    forms.ValidationError(
                        _("The file type {} is not allowed.").format(
                            cleaned_data.get("type")
                        )
                        + " "
                        + _("Allowed file types")
                        + ": "
                        + ", ".join(
                            map(str, dict(allowed_media.UPLOAD_CHOICES).values())
                        ),
                        code="invalid",
                    ),
                )
            cleaned_data["name"] = file.name
            name, extension = splitext(file.name)
            # Replace file extension if it doesn't match it's mime type
            valid_extensions = mimetypes.guess_all_extensions(
                cleaned_data.get("type", "")
            )
            if extension not in valid_extensions and valid_extensions:
                file.name = name + valid_extensions[0]

        if cleaned_data.get("parent_directory"):
            if cleaned_data.get("parent_directory").region != self.instance.region:
                self.add_error(
                    "parent_directory",
                    forms.ValidationError(
                        _(
                            "The file cannot be uploaded to a directory of another region."
                        ),
                        code="invalid",
                    ),
                )

        # If everything looks good until now, generate a thumbnail and an optimized image
        if not self.errors and cleaned_data.get("type").startswith("image"):
            optimized_image = generate_thumbnail(
                file, settings.MEDIA_OPTIMIZED_SIZE, False
            )
            if not optimized_image:
                self.add_error(
                    "file",
                    forms.ValidationError(
                        _("This image file is corrupt."), code="invalid"
                    ),
                )
            else:
                cleaned_data["file"] = optimized_image
                cleaned_data["thumbnail"] = generate_thumbnail(file)

        # Add the calculated file_size and the modification date to the form data
        if cleaned_data.get("file"):
            cleaned_data["file_size"] = cleaned_data.get("file").size
        cleaned_data["last_modified"] = timezone.now()

        logger.debug(
            "UploadMediaFileForm validated [2] with cleaned data %r", cleaned_data
        )
        return cleaned_data
