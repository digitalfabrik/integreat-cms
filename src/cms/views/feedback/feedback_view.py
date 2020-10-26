from django.shortcuts import render
from django.views.generic import TemplateView
from cms.forms.feedback.feedback import FeedbackForm
from cms.models.feedback.event_feedback import EventFeedback
from cms.models.feedback.offer_feedback import OfferFeedback

class FeedbackView(TemplateView):
   template_name= "feedback/feedback_form.html"
   def get(self, request):
        feedback_events = EventFeedback.objects.filter()
        feedback_offers = OfferFeedback.objects.filter()
        return render(request, self.template_name, {'feedback_events': feedback_events, 'feedback_offers': feedback_offers} )

