from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

from integreat_cms.cms.views.utils.opening_hour import get_open_hour_config_data

from ...constants import translation_status

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class POIContextMixin(ContextMixin):
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
        opening_hour_config_data = get_open_hour_config_data(
            can_change_location=self.request.user.has_perm("cms.change_poi")
        )
        context.update(
            {
                "current_menu_item": "pois",
                "translation_status": translation_status,
                "archive_dialog_title": _(
                    "Please confirm that you really want to archive this location",
                ),
                "archive_dialog_text": _(
                    "All translations of this location will also be archived.",
                ),
                "restore_dialog_title": _(
                    "Please confirm that you really want to restore this location",
                ),
                "restore_dialog_text": _(
                    "All translations of this location will also be restored.",
                ),
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this location",
                ),
                "delete_dialog_text": _(
                    "All translations of this location will also be deleted.",
                ),
                "cannot_archive_title": _(
                    "You cannot archive a location which is used by an upcoming event or a contact. \nThis also involves archived events and contacts",
                ),
                "cannot_delete_title": _(
                    "You cannot delete a location which is used by an event or a contact. \nThis also involves archived events and contacts",
                ),
                "opening_hour_config_data": opening_hour_config_data,
            },
        )
        return context
