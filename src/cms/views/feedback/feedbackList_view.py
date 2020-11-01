from django.shortcuts import render
from django.views.generic import TemplateView
from cms.forms.feedback.feedback import FeedbackForm
from cms.models.feedback.event_feedback import EventFeedback
from cms.models.feedback.offer_feedback import OfferFeedback
from cms.models.feedback.region_feedback import RegionFeedback
from cms.models.feedback.page_feedback import PageFeedback


class FeedbackView(TemplateView):
    # template_name = "feedback/feedbackList_form.html"
    template_name = "feedback/feedback_form.html"

    def get(self, request):
        countUp_event = 0
        countUp_offer = 0
        countDown_offer = 0
        countDown_event = 0
        countUp_page = 0
        countDown_page = 0
        countUp_region = 0
        countDown_region = 0
        feedback_events = EventFeedback.objects.filter()
        feedback_offers = OfferFeedback.objects.filter()
        feedback_pages = PageFeedback.objects.filter()
        feedback_regions = RegionFeedback.objects.filter()

        for event in feedback_events:
            if event.emotion == "POS":
                countUp_event = countUp_event + 1
            else:
                countDown_event = countDown_event + 1

        for offer in feedback_offers:
            if offer.emotion == "POS":
                countUp_offer = countUp_offer + 1
            else:
                countDown_offer = countDown_offer + 1

        for page in feedback_pages:
            if page.emotion == "POS":
                countUp_page = countUp_page + 1
            else:
                countDown_page = countDown_page + 1

        for region in feedback_regions:
            if region.emotion == "POS":
                countUp_region = countUp_region + 1
            else:
                countDown_region = countDown_region + 1

        return render(
            request,
            self.template_name,
            {
                "feedback_events": feedback_events,
                "feedback_offers": feedback_offers,
                "feedback_pages": feedback_pages,
                "feedback_regions": feedback_regions,
                "countUp_event": countUp_event,
                "countDown_event": countDown_event,
                "countUp_offer": countUp_offer,
                "countDown_offer": countDown_offer,
                "countUp_page": countUp_page,
                "countDown_page": countDown_page,
                "countUp_region": countUp_region,
                "countDown_region": countDown_region,
            },
        )


"""
    def get(self, request):
        feedbackList_events = EventFeedback.objects.filter(feedback__isnull=False).distinct()
        emotions_events = {}
        for event in feedbackList_events:
         for item in event.feedback:
            emotions_events[item.event]["title"] = event.title
            if item.emotion == "POS":
             emotions_events[item.event]["pos"] = emotions_events[item.event]["pos"] + 1
            else:
              emotions_events[item.event]["neg"] = emotions_events[item.event]["neg"] + 1

        feedbackList_offers = OfferFeedback.objects.filter(feedback__isnull=False).distinct()
        emotions_offers = {}
        for offer in feedbackList_offers:
         for item in offer.feedback:
            emotions_offers[item.offer]["title"] = offer.title
            if item.emotion == "POS":
             emotions_offers[item.offer]["pos"] = emotions_offers[item.offer]["pos"] + 1
            else:
              emotions_offers[item.offer["neg"] = emotions_offers[item.offer]["neg"] + 1

        feedbackList_regions = RegionFeedback.objects.filter(feedback__isnull=False).distinct()
        emotions_regions = {}
        for region  in feedbackList_regions:
         for item in region.feedback:
            emotions_regions[item.region]["title"] = region.title
            if item.emotion == "POS":
             emotions_regions[item.region]["pos"] = emotions_regions[item.region]["pos"] + 1  
            else:
              emotions_regions[item.region]["neg"] = emotions_regions[item.region]["neg"] + 1

        feedbackList_pages = PageFeedback.objects.filter(feedback__isnull=False).distinct()
        emotions_pages = {}
        for page in feedbackList_pages:
         for item in page.feedback:
            emotions_pages[item.page]["title"] = page.title
            if item.emotion == "POS":
             emotions_pages[item.page]["pos"] = emotions_pages[item.page]["pos"] + 1
            else:
              emotions_pages[item.page]["neg"] = emotions_pages[item.page]["neg"] + 1


        return render(
            request,
            self.template_name,
            {
                "feedbackList_events": feedbackList_events,
                "feedbackList_offers": feedbackList_offers,
                "feedbackList_regions": feedbackList_regions,
                "feedbackList_pages": feedbackList_pages,
                "emotions_events": emotions_events,
                "emotions_events": emotions_offers,
                "emotions_events": emotions_regions,
                "emotions_events": emotions_pages,
            }
        )
"""
