from __future__ import annotations

from django.utils.translation import gettext_lazy as _

from ...models import Event
from ..content_version_view import ContentVersionView
from .event_context_mixin import EventContextMixin


# pylint: disable=too-many-ancestors
class EventVersionView(EventContextMixin, ContentVersionView):
    """
    View for browsing the event versions and restoring old event versions
    """

    #: The current content model (see :class:`~django.views.generic.detail.SingleObjectMixin`)
    model = Event

    #: The label of the "back to form" button
    back_to_form_label = _("Back to the event form")
