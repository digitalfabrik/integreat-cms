from __future__ import annotations

from django.utils.translation import gettext_lazy as _

from ...models import Page
from ..content_version_view import ContentVersionView
from .page_context_mixin import PageContextMixin


# pylint: disable=too-many-ancestors
class PageVersionView(PageContextMixin, ContentVersionView):
    """
    View for browsing the page versions and restoring old page versions
    """

    #: The current content model (see :class:`~django.views.generic.detail.SingleObjectMixin`)
    model = Page

    #: The label of the "back to form" button
    back_to_form_label = _("Back to the page form")

    def has_change_permission(self) -> bool:
        """
        Whether the user has the permission to change objects

        :returns: Whether the user can change objects
        """
        return self.request.user.has_perm("cms.change_page_object", self.object)

    def has_publish_permission(self) -> bool:
        """
        Whether the user has the permission to publish objects

        :returns: Whether the user can publish objects
        """
        return self.request.user.has_perm("cms.publish_page_object", self.object)
