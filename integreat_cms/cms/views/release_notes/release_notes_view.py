from __future__ import annotations

from django.views.generic.base import TemplateView

from .release_notes_context_mixin import ReleaseNotesContextMixin


class ReleaseNotesView(TemplateView, ReleaseNotesContextMixin):
    """
    View for retrieving the release notes
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "release_notes/release_notes.html"
