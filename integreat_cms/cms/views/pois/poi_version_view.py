from __future__ import annotations

from django.utils.translation import gettext_lazy as _

from ...models import POI
from ..content_version_view import ContentVersionView
from .poi_context_mixin import POIContextMixin


# pylint: disable=too-many-ancestors
class POIVersionView(POIContextMixin, ContentVersionView):
    """
    View for browsing the POI versions and restoring old POI versions
    """

    #: The current content model (see :class:`~django.views.generic.detail.SingleObjectMixin`)
    model = POI

    #: The label of the "back to form" button
    back_to_form_label = _("Back to the poi form")

    def has_publish_permission(self) -> bool:
        """
        All users who can change POIs also can publish these changes

        :returns: Whether the user can publish POIs
        """
        return self.has_change_permission()
