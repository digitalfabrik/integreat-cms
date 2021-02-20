from datetime import date

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...constants import feedback_ratings
from ...decorators import region_permission_required
from ...models import Feedback, Region


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class RegionFeedbackListView(PermissionRequiredMixin, TemplateView):
    """
    View to list all region feedback (content feedback)
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_feedback"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "feedback/region_feedback_list.html"

    # pylint: disable=too-many-locals
    def get(self, request, *args, **kwargs):
        """
        Render region feedback list

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        # current region
        region = Region.get_current_region(request)

        region_feedback = Feedback.objects.filter(region=region, is_technical=False)

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "region_feedback",
                "region_feedback": region_feedback,
            },
        )
