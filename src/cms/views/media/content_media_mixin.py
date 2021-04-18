from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import ContextMixin

from django.urls import reverse

from ...models import Region

# pylint: disable=too-few-public-methods
class ContentMediaMixin(ContextMixin):
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
                "btn_upload": _("Upload File"),
                "btn_delete": _("Delete File"),
                "btn_update": _("Update File"),
                "btn_create_directory": _("Create Directory"),
                "btn_upload_file": _("Upload File"),
                "btn_back": _("Back"),
                "btn_submit": _("Submit"),
                "btn_select": _("Select"),
                "btn_save": _("Save File"),
                "label_media_library": _("Media Library"),
                "label_media_root": _("Home"),
                "label_file_name": _("File Name:"),
                "label_directory_name": _("Directory Name:"),
                "label_data_type": _("Filetype:"),
                "label_data_uploaded": _("File uploaded:"),
                "label_alt_text": _("Alternative Text:"),
                "message_suc": _("Success"),
            },
        }
        kwargs = {"region_slug": region.slug} if region else {}
        media_config_data["apiEndpoints"] = {
            "getDirectoryContent": reverse(
                "mediacenter_get_directory_content",
                kwargs=kwargs,
            ),
            "editMediaUrl": reverse("mediacenter_edit_url", kwargs=kwargs),
            "createDirectory": reverse("mediacenter_create_directory", kwargs=kwargs),
            "deleteDirecotry": reverse("mediacenter_delete_directory", kwargs=kwargs),
            "updateDirectory": reverse("mediacenter_update_directory", kwargs=kwargs),
            "uploadFile": reverse("mediacenter_upload_file", kwargs=kwargs),
            "deleteMediaUrl": reverse("mediacenter_delete_file", kwargs=kwargs),
            "getDirectoryPath": reverse("mediacenter_directory_path", kwargs=kwargs),
        }

        context["media_config_data"] = media_config_data
        return context
