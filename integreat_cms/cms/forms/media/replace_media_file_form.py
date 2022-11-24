import logging
import os


import magic

from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _

from ...constants import allowed_media
from ...models import MediaFile
from ...utils.media_utils import generate_thumbnail
from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class ReplaceMediaFileForm(CustomModelForm):
    """
    Form for replacing media file objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = MediaFile
        #: The fields of the model which should be handled by this form
        fields = ("file", "name", "thumbnail", "file_size", "last_modified")

    def __init__(self, data=None, files=None, instance=None):
        """
        Initialize UploadMediaFileForm form

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
        self.fields["thumbnail"].required = False
        self.fields["file_size"].required = False
        self.fields["last_modified"].required = False

        self.original_file_path = instance.file.path
        self.original_thumbnail_path = (
            instance.thumbnail.path if instance.thumbnail else None
        )

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`:
        Check whether a file was uploaded and whether it's type matches the original file's type.
        If the file type is invalid, add a :class:`~django.core.exceptions.ValidationError`.

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()

        file = cleaned_data.get("file")

        # Only validate type if a file is uploaded - otherwise, the form throws an error anyways
        if file:
            # Check magic bytes for actual file type - the content_type of the file can easily be forged
            new_type = magic.from_buffer(file.read(), mime=True)
            if new_type != self.instance.type:
                # Check whether we have a more readable version of the mime type
                new_type_display = dict(allowed_media.CHOICES).get(new_type, new_type)
                self.add_error(
                    "file",
                    forms.ValidationError(
                        _(
                            "The file type of the new file ({}) does not match the original file's type ({})."
                        ).format(new_type_display, self.instance.get_type_display())
                    ),
                )

            # Set the visible name in the database to the filename of the new file
            cleaned_data["name"] = file.name

        # If everything looks good until now, generate a thumbnail and an optimized image
        if not self.errors and self.instance.type.startswith("image"):
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

        # Add the calculated file_size to the form data
        if cleaned_data.get("file"):
            cleaned_data["file_size"] = cleaned_data.get("file").size
        cleaned_data["last_modified"] = timezone.now()

        logger.debug(
            "ReplaceMediaFileForm validated [2] with cleaned data %r", cleaned_data
        )
        return cleaned_data

    def save(self, commit=True):
        # Remove old file
        os.remove(self.original_file_path)
        logger.debug("Removed old file %r", self.original_file_path)

        # Remove old thumbnail
        if self.original_thumbnail_path:
            os.remove(self.original_thumbnail_path)
            logger.debug("Removed old thumbnail %r", self.original_thumbnail_path)

        super().save(commit=commit)
