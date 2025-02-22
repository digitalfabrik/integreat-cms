from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

if TYPE_CHECKING:
    from typing import Any


class ContactContextMixin(ContextMixin):
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
                "current_menu_item": "contacts",
                "archive_dialog_title": _(
                    "Please confirm that you really want to archive this contact",
                ),
                "restore_dialog_title": _(
                    "Please confirm that you really want to restore this contact",
                ),
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this contact",
                ),
            },
        )

        return context
