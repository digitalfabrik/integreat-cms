from django.shortcuts import render
from django.http import HttpResponse
from .forms import FeedbackForm


def Feedback(request):
    form = FeedbackForm()
    return render(request, 'feedback_form.html', {'form':form})