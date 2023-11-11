from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.views.generic.base import ContextMixin

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ImprintContextMixin(ContextMixin):
    """
    This mixin provides extra context for imprint views
    """

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_menu_item": "imprint",
                "IMPRINT_SLUG": settings.IMPRINT_SLUG,
            }
        )
        return context
