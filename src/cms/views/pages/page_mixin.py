from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import ContextMixin


# pylint: disable=too-few-public-methods
class PageMixin(ContextMixin):
    extra_context = {
        "archive_dialog_title": _(
            "Please confirm that you really want to archive this page"
        ),
        "archive_dialog_text": format_lazy(
            "{} {}",
            _("All subpages of this page are automatically archived as well."),
            _("This affects all translations."),
        ),
        "restore_dialog_title": _(
            "Please confirm that you really want to restore this page"
        ),
        "restore_dialog_text": format_lazy(
            "{} {} {}",
            _(
                "All subpages of this page that were not already archived before this page are also restored."
            ),
            _("Please check the subpages after the process is complete."),
            _("This affects all translations."),
        ),
        "delete_dialog_title": _(
            "Please confirm that you really want to delete this page"
        ),
        "delete_dialog_text": _("All translations of this page will also be deleted."),
    }
