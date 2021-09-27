from django.utils.translation import ugettext as _
from django.views.generic.base import ContextMixin

from django.urls import reverse

from ...constants import allowed_media
from ...models import Region

# pylint: disable=too-few-public-methods
class MediaContextMixin(ContextMixin):
    """
    This mixin provides context data required by the the media library.
    """

    def get_context_data(self, **kwargs):
        """
        Overwrites the default :meth:`~django.views.generic.base.ContextMixin.get_context_data` Method of Django to provide an additional context for template rendering.

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The overwritten context.
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        region = Region.get_current_region(self.request)

        media_config_data = {
            "mediaTranslations": {
                # Headings are capitalized
                "heading_media_library": _("Media Library"),
                "heading_create_directory": _("Create Directory"),
                "heading_upload_file": _("Upload File"),
                "heading_media_root": _("Home"),
                "heading_directory_properties": _("Directory Properties"),
                "heading_file_properties": _("File Properties"),
                "btn_upload": _("Upload"),
                "btn_upload_file": _("Upload file"),
                "btn_save_file": _("Save file"),
                "btn_delete_file": _("Delete file"),
                "btn_show_file": _("Show file"),
                "btn_create": _("Create"),
                "btn_enter_directory": _("Enter directory"),
                "btn_create_directory": _("Create directory"),
                "btn_rename_directory": _("Rename directory"),
                "btn_delete_directory": _("Delete directory"),
                "btn_delete_empty_directory": _(
                    "You can only delete empty directories"
                ),
                "btn_back": _("Back"),
                "btn_close": _("Close detail view"),
                "btn_submit": _("Submit"),
                "btn_select": _("Select"),
                "btn_select_file": _("Select file"),
                "label_file_name": _("File name:"),
                "label_url": _("URL") + ":",
                "label_directory_name": _("Directory name:"),
                "label_data_type": _("Filetype:"),
                "label_file_uploaded": _("File uploaded on:"),
                "label_directory_created": _("Directory created on:"),
                "label_alt_text": _("Alternative text:"),
                "text_enter_directory_name": _("Enter directory name here"),
                "text_file_readonly": _("This file is read-only and cannot be edited."),
                "text_dir_readonly": _(
                    "This directory is read-only and cannot be edited."
                ),
                "text_only_image": _("Only images can be selected as an icon."),
                "text_file_delete_confirm": _(
                    "Please confirm that you really want to delete this file"
                ),
                "text_dir_delete_confirm": _(
                    "Please confirm that you really want to delete this directory"
                ),
                "text_error": (
                    _("An error has occurred.") + " " + _("Please try again later.")
                ),
                "text_network_error": (
                    _("A network error has occurred.")
                    + " "
                    + _("Please try again later.")
                ),
            },
            "expertMode": self.request.user.expert_mode,
            "allowedMediaTypes": ", ".join(dict(allowed_media.CHOICES)),
        }
        kwargs = {"region_slug": region.slug} if region else {}
        media_config_data["apiEndpoints"] = {
            "getDirectoryPath": reverse("mediacenter_directory_path", kwargs=kwargs),
            "getDirectoryContent": reverse(
                "mediacenter_get_directory_content",
                kwargs=kwargs,
            ),
            "createDirectory": reverse("mediacenter_create_directory", kwargs=kwargs),
            "editDirectory": reverse("mediacenter_edit_directory", kwargs=kwargs),
            "deleteDirectory": reverse("mediacenter_delete_directory", kwargs=kwargs),
            "uploadFile": reverse("mediacenter_upload_file", kwargs=kwargs),
            "editFile": reverse("mediacenter_edit_file", kwargs=kwargs),
            "deleteFile": reverse("mediacenter_delete_file", kwargs=kwargs),
        }

        context["media_config_data"] = media_config_data
        return context
