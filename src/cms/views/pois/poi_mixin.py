from django.utils.translation import ugettext_lazy
from django.views.generic.base import ContextMixin

# pylint: disable=too-few-public-methods
class POIMixin(ContextMixin):
    extra_context = {
        "archive_dialog_title": ugettext_lazy(
            "Please confirm that you really want to archive this location"
        ),
        "archive_dialog_text": ugettext_lazy(
            "All translations of this location will also be archived."
        ),
        "restore_dialog_title": ugettext_lazy(
            "Please confirm that you really want to restore this location"
        ),
        "restore_dialog_text": ugettext_lazy(
            "All translations of this location will also be restored."
        ),
        "delete_dialog_title": ugettext_lazy(
            "Please confirm that you really want to delete this location"
        ),
        "delete_dialog_text": ugettext_lazy(
            "All translations of this location will also be deleted."
        ),
    }
