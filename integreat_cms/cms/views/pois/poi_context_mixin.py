import logging

from django.utils.translation import ugettext_lazy
from django.views.generic.base import ContextMixin

from ...constants import translation_status

logger = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
class POIContextMixin(ContextMixin):
    """
    This mixin provides extra context for language tree views
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
                "translation_status": translation_status,
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
        )
        return context
