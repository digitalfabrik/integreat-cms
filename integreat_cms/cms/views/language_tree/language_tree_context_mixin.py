import logging

from django.utils.translation import ugettext as _
from django.views.generic.base import ContextMixin

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class LanguageTreeContextMixin(ContextMixin):
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
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this language node"
                ),
                "delete_dialog_text": _(
                    "All translations for pages, locations, events and push notifications of this language will also be deleted."
                ),
            }
        )
        return context
