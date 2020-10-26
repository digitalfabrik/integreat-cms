from django import forms
from ...models import Feedback
#from ...constants import feedback_emotions
#from cms.constants import feedback_emotions

class FeedbackForm(forms.Form):
   class Meta:
        model = Feedback 
        fields = ["emotion", 
                  "comment",
                  " is_technical"]
