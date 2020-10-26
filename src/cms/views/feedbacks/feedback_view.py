from django.shortcuts import render
from django.views.generic import TemplateView
from cms.forms.feedbacks.feedback import FeedbackForm


class FeedbackView(TemplateView):
   template_name= "feedbacks/feedback_form.html"
   def get(self, request):
        form = FeedbackForm()
        return render(request, self.template_name, {'form': form} )
       