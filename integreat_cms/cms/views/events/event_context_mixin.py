from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class EventContextMixin(ContextMixin):
    """
    This mixin provides extra context for event views
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
                "current_menu_item": "events_form",
                "archive_dialog_title": _(
                    "Please confirm that you really want to archive this event"
                ),
                "archive_dialog_text": _(
                    "All translations of this event will also be archived."
                ),
                "restore_dialog_title": _(
                    "Please confirm that you really want to restore this event"
                ),
                "restore_dialog_text": _(
                    "All translations of this event will also be restored."
                ),
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this event"
                ),
                "delete_dialog_text": _(
                    "All translations of this event will also be deleted."
                ),
            }
        )
        return context
