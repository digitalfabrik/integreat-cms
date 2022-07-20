import logging

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import AdminFeedbackFilterForm
from ...models import Feedback

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_feedback"), name="dispatch")
class AdminFeedbackListView(TemplateView):
    """
    View to list all admin feedback (technical feedback)
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "feedback/admin_feedback_list.html"

    def get(self, request, *args, **kwargs):
        r"""
        Render admin feedback list

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        admin_feedback = Feedback.objects.filter(is_technical=True)

        # Filter pages according to given filters, if any
        filter_form = AdminFeedbackFilterForm(data=request.GET)
        admin_feedback, query = filter_form.apply(admin_feedback, region=None)

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
                "filter_form": filter_form,
                "search_query": query,
            },
        )
