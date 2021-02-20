from datetime import date

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...constants import feedback_ratings
from ...decorators import staff_required
from ...models import Feedback


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class AdminFeedbackListView(PermissionRequiredMixin, TemplateView):
    """
    View to list all admin feedback (technical feedback)
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_feedback"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "feedback/admin_feedback_list.html"

    def get(self, request, *args, **kwargs):
        """
        Render admin feedback list

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        admin_feedback = Feedback.objects.filter(is_technical=True)

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "admin_feedback",
                "admin_feedback": admin_feedback,
            },
        )
