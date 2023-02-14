from django.utils.translation import gettext as _
from django.views.generic.base import ContextMixin

from django.urls import reverse

from ...constants import allowed_media


# pylint: disable=too-few-public-methods
class MediaContextMixin(ContextMixin):
    """
    This mixin provides context data required by the the media library.
    """

    def get_context_data(self, **kwargs):
        r"""
        Overwrites the default :meth:`~django.views.generic.base.ContextMixin.get_context_data` Method of Django to provide an additional context for template rendering.

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The overwritten context.
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)

        media_config_data = {
            "mediaTranslations": {
                # Headings are capitalized
                "heading_media_library": _("Media Library"),
                "heading_create_directory": _("Create Directory"),
                "heading_upload_file": _("Upload File"),
                "text_upload_area": _("Click or drop files here for upload."),
                "heading_media_root": _("Home"),
                "heading_directory_properties": _("Directory Properties"),
                "heading_file_properties": _("File Properties"),
                "heading_search_results": _("Search results for"),
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
                "btn_replace_file": _("Replace file"),
                "btn_search": _("Search"),
                "label_file_name": _("File name:"),
                "label_url": _("URL") + ":",
                "label_directory_name": _("Directory name:"),
                "label_data_type": _("File format:"),
                "label_file_size": _("File size:"),
                "label_file_uploaded": _("File uploaded on:"),
                "label_file_modified": _("File modified on:"),
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
                "text_error_invalid_file_type": _(
                    "This file type is not supported. Supported types are:"
                ),
                "text_error": (
                    _("An error has occurred.") + " " + _("Please try again later.")
                ),
                "text_network_error": (
                    _("A network error has occurred.")
                    + " "
                    + _("Please try again later.")
                ),
                "text_allowed_media_types": ", ".join(
                    map(str, dict(allowed_media.UPLOAD_CHOICES).values())
                ),
            },
            "expertMode": self.request.user.expert_mode,
            "allowedMediaTypes": ", ".join(dict(allowed_media.UPLOAD_CHOICES)),
            "canDeleteFile": self.request.user.has_perm("cms.delete_mediafile"),
            "canReplaceFile": self.request.user.has_perm("cms.replace_mediafile"),
            "canDeleteDirectory": self.request.user.has_perm("cms.delete_directory"),
        }
        kwargs = (
            {"region_slug": self.request.region.slug} if self.request.region else {}
        )
        media_config_data["apiEndpoints"] = {
            "getDirectoryPath": reverse("mediacenter_directory_path", kwargs=kwargs),
            "getDirectoryContent": reverse(
                "mediacenter_get_directory_content",
                kwargs=kwargs,
            ),
            "getSearchResult": reverse(
                "mediacenter_get_search_result",
                kwargs=kwargs,
            ),
            "getSearchSuggestions": reverse(
                "search_content_ajax",
                kwargs=kwargs,
            ),
            "createDirectory": reverse("mediacenter_create_directory", kwargs=kwargs),
            "editDirectory": reverse("mediacenter_edit_directory", kwargs=kwargs),
            "deleteDirectory": reverse("mediacenter_delete_directory", kwargs=kwargs),
            "uploadFile": reverse("mediacenter_upload_file", kwargs=kwargs),
            "editFile": reverse("mediacenter_edit_file", kwargs=kwargs),
            "moveFile": reverse("mediacenter_move_file", kwargs=kwargs),
            "deleteFile": reverse("mediacenter_delete_file", kwargs=kwargs),
            "replaceFile": reverse("mediacenter_replace_file", kwargs=kwargs),
        }

        context["media_config_data"] = media_config_data
        return context
