from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class LanguageTreeContextMixin(ContextMixin):
    """
    This mixin provides extra context for language tree views
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
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this language node"
                ),
                "delete_dialog_text": _(
                    "All translations for pages, locations, events and push notifications of this language will also be deleted."
                ),
            }
        )
        return context
