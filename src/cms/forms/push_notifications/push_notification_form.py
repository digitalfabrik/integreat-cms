from django import forms

from ...models import PushNotification, PushNotificationTranslation


class PushNotificationForm(forms.ModelForm):
    """
    Form for creating and modifying push notification objects
    """

    class Meta:
        model = PushNotification
        fields = ["channel", "mode"]


class PushNotificationTranslationForm(forms.ModelForm):
    """
    Form for creating and modifying push notification translation objects
    """

    class Meta:
        model = PushNotificationTranslation
        fields = ["title", "text", "language"]
