from __future__ import annotations

from django.utils.translation import gettext_lazy as _

from ...models import Place
from ..content_version_view import ContentVersionView
from .place_context_mixin import PlaceContextMixin


class PlaceVersionView(PlaceContextMixin, ContentVersionView):
    """
    View for browsing the place versions and restoring old place versions
    """

    #: The current content model (see :class:`~django.views.generic.detail.SingleObjectMixin`)
    model = Place

    #: The label of the "back to form" button
    back_to_form_label = _("Back to the place form")

    def has_publish_permission(self) -> bool:
        """
        All users who can change places also can publish these changes

        :returns: Whether the user can publish places
        """
        return self.has_change_permission()
