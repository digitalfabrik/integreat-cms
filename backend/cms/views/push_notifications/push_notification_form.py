"""
Form for creating a user object
"""

from django import forms
from ...models.push_notification import PushNotification, PushNotificationTranslation


class PushNotificationForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = PushNotification
        fields = ['channel']

    def __init__(self, *args, **kwargs):
        super(PushNotificationForm, self).__init__(*args, **kwargs)

class PushNotificationTranslationForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = PushNotificationTranslation
        fields = ['title', 'text']

    def __init__(self, *args, **kwargs):
        super(PushNotificationTranslationForm, self).__init__(*args, **kwargs)
