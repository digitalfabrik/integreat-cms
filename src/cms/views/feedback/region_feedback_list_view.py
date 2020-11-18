from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...constants import feedback_emotions
from ...decorators import region_permission_required
from ...models import (
    Region,
    PageFeedback,
    EventFeedback,
    Feedback,
)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class RegionFeedbackListView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.view_feedback"
    raise_exception = True
    template_name = "feedback/region_feedback_list.html"

    # pylint: disable=too-many-locals
    def get(self, request, *args, **kwargs):
        # current region
        region = Region.get_current_region(request)

        page_feedback = PageFeedback.objects.filter(
            page_translation__page__region=region, is_technical=False
        )
        event_feedback = EventFeedback.objects.filter(
            event_translation__event__region=region, is_technical=False
        )
        event_list_feedback = region.event_list_feedback.filter(is_technical=False)
        offer_feedback = region.offer_feedback.filter(is_technical=False)
        offer_list_feedback = region.offer_list_feedback.filter(
            region=region, is_technical=False
        )
        search_result_feedback = region.search_result_feedback.filter(
            is_technical=False
        )
        imprint_page_feedback = region.imprint_page_feedback.filter(is_technical=False)
        region_feedback = region.feedback.filter(is_technical=False)

        feedback_exists = Feedback.objects.filter(is_technical=False).exists()

        page_count_pos = page_feedback.filter(emotion=feedback_emotions.POS).count()
        page_count_neg = page_feedback.filter(emotion=feedback_emotions.NEG).count()
        event_count_pos = event_feedback.filter(emotion=feedback_emotions.POS).count()
        event_count_neg = event_feedback.filter(emotion=feedback_emotions.NEG).count()
        offer_count_pos = offer_feedback.filter(emotion=feedback_emotions.POS).count()
        offer_count_neg = offer_feedback.filter(emotion=feedback_emotions.NEG).count()

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "region_feedback",
                "page_feedback": page_feedback,
                "event_feedback": event_feedback,
                "event_list_feedback": event_list_feedback,
                "offer_list_feedback": offer_list_feedback,
                "search_result_feedback": search_result_feedback,
                "imprint_page_feedback": imprint_page_feedback,
                "region_feedback": region_feedback,
                "page_count_pos": page_count_pos,
                "page_count_neg": page_count_neg,
                "event_count_pos": event_count_pos,
                "event_count_neg": event_count_neg,
                "offer_count_pos": offer_count_pos,
                "offer_count_neg": offer_count_neg,
                "feedback_exists": feedback_exists,
            },
        )
