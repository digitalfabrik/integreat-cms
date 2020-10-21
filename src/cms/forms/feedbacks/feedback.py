from django import forms

from ...constants import feedback_emotions

class FeedbackForm(forms.Form):
    emotion = forms.CharField(max_length=3, choices=feedback_emotions.CHOICES)
    comment = forms.CharField(max_length=1000)
    is_technical = forms.BooleanField()