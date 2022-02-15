import logging

from datetime import date

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...constants import feedback_ratings, feedback_read_status
from ...decorators import permission_required
from ...forms import RegionFeedbackFilterForm
from ...models import Feedback

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_feedback"), name="dispatch")
class RegionFeedbackListView(TemplateView):
    """
    View to list all region feedback (content feedback)
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "feedback/region_feedback_list.html"

    # pylint: disable=too-many-locals
    def get(self, request, *args, **kwargs):
        r"""
        Render region feedback list

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        # current region
        region = request.region

        region_feedback = Feedback.objects.filter(region=region, is_technical=False)

        query = None

        # Filter pages according to given filters, if any
        filter_data = kwargs.get("filter_data")
        if filter_data:
            # Set data for filter form rendering
            filter_form = RegionFeedbackFilterForm(data=filter_data)
            if filter_form.is_valid():
                query = filter_form.cleaned_data["query"]
                if query:
                    region_feedback = Feedback.search(region, query)

                # Filter feedback for language
                if filter_form.cleaned_data["language"]:
                    region_feedback = region_feedback.filter(
                        language=filter_form.cleaned_data["language"]
                    )
                # Filter feedback for category
                if filter_form.cleaned_data["category"]:
                    # Inherited models automatically get their name as lowercase assigned as reverse relationship from the base class
                    filter_condition = (
                        filter_form.cleaned_data["category"].lower() + "__isnull"
                    )
                    region_feedback = region_feedback.filter(
                        **{filter_condition: False}
                    )
                # Filter feedback for timerange
                region_feedback = region_feedback.filter(
                    created_date__date__gte=filter_form.cleaned_data["date_from"]
                    or date.min,
                    created_date__date__lte=filter_form.cleaned_data["date_to"]
                    or date.max,
                )
                # Filter feedback for their read status (skip filtering if either both or no checkboxes are checked)
                read_status = filter_form.cleaned_data["read_status"]
                if read_status == [feedback_read_status.READ]:
                    region_feedback = region_feedback.filter(read_by__isnull=False)
                elif read_status == [feedback_read_status.UNREAD]:
                    region_feedback = region_feedback.filter(read_by__isnull=True)
                # Filter feedback for ratings (skip filtering if either all or no checkboxes are checked)
                if (
                    len(filter_form.cleaned_data["rating"])
                    != len(feedback_ratings.FILTER_CHOICES)
                    and len(filter_form.cleaned_data["rating"]) != 0
                ):
                    if "" in filter_form.cleaned_data["rating"]:
                        feedback_without_rating = region_feedback.filter(
                            rating__isnull=True
                        )

                    region_feedback = region_feedback.filter(
                        rating__in=filter_form.cleaned_data["rating"]
                    )

                    if "" in filter_form.cleaned_data["rating"]:
                        region_feedback = region_feedback.union(feedback_without_rating)
            print(filter_form.errors)
        else:
            filter_form = RegionFeedbackFilterForm()
            filter_form.changed_data.clear()

        region_feedback = region_feedback.select_related("region", "language")

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        paginator = Paginator(region_feedback, chunk_size)
        chunk = request.GET.get("page")
        region_feedback_chunk = paginator.get_page(chunk)

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "region_feedback",
                "region_feedback": region_feedback_chunk,
                "filter_form": filter_form,
                "search_query": query,
            },
        )

    def post(self, request, *args, **kwargs):
        r"""
        Render feedback list with applied filters

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return self.get(request, *args, **kwargs, filter_data=request.POST)
