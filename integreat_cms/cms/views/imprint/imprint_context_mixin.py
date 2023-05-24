import logging

from django.conf import settings
from django.views.generic.base import ContextMixin

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ImprintContextMixin(ContextMixin):
    """
    This mixin provides extra context for imprint views
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
                "current_menu_item": "imprint",
                "IMPRINT_SLUG": settings.IMPRINT_SLUG,
            }
        )
        return context
