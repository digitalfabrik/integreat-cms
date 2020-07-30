from django import forms

from ...models import PushNotification, PushNotificationTranslation


class PushNotificationForm(forms.ModelForm):
    """
    Form for creating and modifying push notification objects
    """

    class Meta:
        model = PushNotification
        fields = ["channel"]

    def __init__(self, *args, **kwargs):
        super(PushNotificationForm, self).__init__(*args, **kwargs)


class PushNotificationTranslationForm(forms.ModelForm):
    """
    Form for creating and modifying push notification translation objects
    """

    class Meta:
        model = PushNotificationTranslation
        fields = ["title", "text"]

    def __init__(self, *args, **kwargs):
        super(PushNotificationTranslationForm, self).__init__(*args, **kwargs)
