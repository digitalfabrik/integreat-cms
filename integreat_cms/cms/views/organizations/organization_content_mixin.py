from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class OrganizationContextMixin(ContextMixin):
    """
    This mixin provides extra context for organization views
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
                "current_menu_item": "organization_form",
                "archive_dialog_title": _(
                    "Please confirm that you really want to archive this organization",
                ),
                "archive_dialog_text": _(
                    "Archiving this organization removes it from all users and content objects that use it",
                ),
                "restore_dialog_title": _(
                    "Please confirm that you really want to restore this organization",
                ),
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this organization",
                ),
                "delete_dialog_text": _(
                    "Deleting this organization removes it from all users and content objects that use it",
                ),
                "cannot_archive_title": _(
                    "You cannot archive an organization which is used by a poi, page or user. \nThis also involves archived pages and pois",
                ),
                "cannot_delete_title": _(
                    "You cannot delete an organization which is used by a poi, page or user. \nThis also involves archived pages and pois",
                ),
            },
        )
        return context
