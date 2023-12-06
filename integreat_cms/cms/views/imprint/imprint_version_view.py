from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Any

from ...models import ImprintPage
from ..content_version_view import ContentVersionView
from .imprint_context_mixin import ImprintContextMixin


# pylint: disable=too-many-ancestors
class ImprintVersionView(ImprintContextMixin, ContentVersionView):
    """
    View for browsing the imprint versions and restoring old imprint versions
    """

    #: The current content model (see :class:`~django.views.generic.detail.SingleObjectMixin`)
    model = ImprintPage

    #: The label of the "back to form" button
    back_to_form_label = _("Back to the imprint form")

    @property
    def edit_url(self) -> str:
        """
        The url to the form in the current language

        :returns: The edit url
        """
        if TYPE_CHECKING:
            assert self.language
        return reverse(
            "edit_imprint",
            kwargs={
                "region_slug": self.request.region.slug,
                "language_slug": self.language.slug,
            },
        )

    @property
    def versions_url(self) -> str:
        """
        The url to the form in the current language

        :returns: The edit url
        """
        if TYPE_CHECKING:
            assert self.language
        return reverse(
            "imprint_versions",
            kwargs={
                "region_slug": self.request.region.slug,
                "language_slug": self.language.slug,
            },
        )

    def get_object(self, queryset: Any | None = None) -> ImprintPage:
        """
        Get the current imprint object

        :raises ~django.http.Http404: HTTP status 404 if the imprint is not found

        :return: The imprint object
        """
        if not (imprint := self.request.region.imprint):
            raise Http404("No imprint found for this region")
        return imprint

    def has_publish_permission(self) -> bool:
        """
        All users who can change the imprint also can publish these changes

        :returns: Whether the user can publish the imprint
        """
        return self.has_change_permission()
