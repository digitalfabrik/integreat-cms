import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import ContextMixin

from ...constants import translation_status, status
from ...utils.translation_utils import ugettext_many_lazy as __

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class PageContextMixin(ContextMixin):
    """
    This mixin provides extra context for page views
    """

    def get_context_data(self, **kwargs):
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_menu_item": "pages",
                "translation_status": translation_status,
                "PUBLIC": status.PUBLIC,
                "WEBAPP_URL": settings.WEBAPP_URL,
                "archive_dialog_title": _(
                    "Please confirm that you really want to archive this page"
                ),
                "archive_dialog_text": __(
                    _("All subpages of this page are automatically archived as well."),
                    _("This affects all translations."),
                ),
                "restore_dialog_title": _(
                    "Please confirm that you really want to restore this page"
                ),
                "restore_dialog_text": __(
                    _(
                        "All subpages of this page that were not already archived before this page are also restored."
                    ),
                    _("Please check the subpages after the process is complete."),
                    _("This affects all translations."),
                ),
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this page"
                ),
                "delete_dialog_text": _(
                    "All translations of this page will also be deleted."
                ),
            }
        )
        return context
