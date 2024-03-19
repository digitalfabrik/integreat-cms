from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import magic
from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ...constants import allowed_media
from ...models import MediaFile, User
from ...utils.linkcheck_utils import replace_links
from ...utils.media_utils import generate_thumbnail
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from django.http import QueryDict
    from django.utils.datastructures import MultiValueDict

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
        fields: tuple[str, ...] = (
            "file",
            "name",
            "thumbnail",
            "file_size",
            "last_modified",
        )

    def __init__(
        self,
        user: User | None = None,
        data: QueryDict | None = None,
        files: MultiValueDict | None = None,
        instance: MediaFile | None = None,
    ) -> None:
        """
        Initialize UploadMediaFileForm form

        :param data: A dictionary-like object containing all given HTTP POST parameters
        :param files: A dictionary-like object containing all uploaded files
        :param instance: This form's instance
        """

        if TYPE_CHECKING:
            assert instance

        # instantiate ModelForm
        super().__init__(data=data, files=files, instance=instance)

        # Make fields not required because they're filled automatically
        self.fields["name"].required = False
        self.fields["thumbnail"].required = False
        self.fields["file_size"].required = False
        self.fields["last_modified"].required = False

        self.original_file_url = instance.url
        self.original_file_path = instance.file.path
        self.original_thumbnail_path = (
            instance.thumbnail.path if instance.thumbnail else None
        )

        self.user = user

    def clean(self) -> dict:
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`:
        Check whether a file was uploaded and whether it's type matches the original file's type.
        If the file type is invalid, add a :class:`~django.core.exceptions.ValidationError`.

        :return: The cleaned form data
        """
        cleaned_data = super().clean()

        # Only validate type if a file is uploaded - otherwise, the form throws an error anyways
        if file := cleaned_data.get("file"):
            # Check magic bytes for actual file type - the content_type of the file can easily be forged
            if (
                new_type := magic.from_buffer(file.read(), mime=True)
            ) != self.instance.type:
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
            if optimized_image := generate_thumbnail(
                file, settings.MEDIA_OPTIMIZED_SIZE, False
            ):
                cleaned_data["file"] = optimized_image
                cleaned_data["thumbnail"] = generate_thumbnail(file)
            else:
                self.add_error(
                    "file",
                    forms.ValidationError(
                        _("This image file is corrupt."), code="invalid"
                    ),
                )
        # Add the calculated file_size to the form data
        if file := cleaned_data.get("file"):
            cleaned_data["file_size"] = file.size
        cleaned_data["last_modified"] = timezone.now()

        logger.debug(
            "ReplaceMediaFileForm validated [2] with cleaned data %r", cleaned_data
        )
        return cleaned_data

    def save(self, commit: bool = True) -> MediaFile:
        if commit:
            # Remove old file
            try:
                os.remove(self.original_file_path)
                logger.debug("Removed old file %r", self.original_file_path)
            except FileNotFoundError:
                logger.debug(
                    "The file %r could not be removed", self.original_file_path
                )
            # Remove old thumbnail
            if self.original_thumbnail_path:
                os.remove(self.original_thumbnail_path)
                logger.debug("Removed old thumbnail %r", self.original_thumbnail_path)

        result = super().save(commit=commit)

        # Update the file url in content
        new_url = self.instance.url
        assert self.original_file_url
        replace_links(
            self.original_file_url,
            new_url,
            commit=commit,
            user=self.user,
            region=self.instance.region,
        )

        return result
