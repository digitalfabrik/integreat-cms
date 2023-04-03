import logging

from django.views.generic import TemplateView

from ...models import Feedback
from ..chat.chat_context_mixin import ChatContextMixin
from ..release_notes.release_notes_context_mixin import ReleaseNotesContextMixin

logger = logging.getLogger(__name__)


class AdminDashboardView(TemplateView, ChatContextMixin, ReleaseNotesContextMixin):
    """
    View for the admin dashboard
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "dashboard/admin_dashboard.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "admin_dashboard"}
    #: Whether only the latest release notes should be included
    only_latest_release = True

    def get_context_data(self, **kwargs):
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context["admin_feedback"] = Feedback.objects.filter(
            is_technical=True,
            read_by=None,
            archived=False,
        )[:5]
        return context
