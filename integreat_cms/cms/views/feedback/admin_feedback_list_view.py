from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import AdminFeedbackFilterForm
from ...models import Feedback

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_feedback"), name="dispatch")
class AdminFeedbackListView(TemplateView):
    """
    View to list all admin feedback (technical feedback)
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template = "feedback/admin_feedback_list.html"
    template_archived = "feedback/admin_feedback_list_archived.html"

    #: Whether or not to show archived feedback
    archived = False

    @property
    def template_name(self) -> str:
        """
        Select correct HTML template, depending on :attr:`~integreat_cms.cms.views.feedback.admin_feedback_list_view.AdminFeedbackListView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        """
        return self.template_archived if self.archived else self.template

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render admin feedback list

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        admin_feedback = Feedback.objects.filter(
            is_technical=True, archived=self.archived
        )

        # Filter pages according to given filters, if any
        filter_form = AdminFeedbackFilterForm(data=request.GET)
        admin_feedback, query = filter_form.apply(admin_feedback)

        admin_feedback = admin_feedback.select_related("region", "language")

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        paginator = Paginator(admin_feedback, chunk_size)
        chunk = request.GET.get("page")
        admin_feedback_chunk = paginator.get_page(chunk)

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "admin_feedback",
                "admin_feedback": admin_feedback_chunk,
                "archived_count": Feedback.objects.filter(
                    is_technical=True, archived=True
                ).count(),
                "filter_form": filter_form,
                "search_query": query,
            },
        )
