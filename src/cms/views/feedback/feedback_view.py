from django.shortcuts import render
from django.views.generic import TemplateView
from cms.forms.feedback.feedback import FeedbackForm


class FeedbackView(TemplateView):
   template_name= "feedback/feedback_form.html"
   def get(self, request):
        form = FeedbackForm()
        return render(request, self.template_name, {'form': form} )
       
