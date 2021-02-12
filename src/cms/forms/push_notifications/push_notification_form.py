from django import forms

from ..placeholder_model_form import PlaceholderModelForm
from ...models import PushNotification, PushNotificationTranslation


class PushNotificationForm(forms.ModelForm):
    """
    Form for creating and modifying push notification objects
    """

    class Meta:
        model = PushNotification
        fields = ["channel", "mode"]


class PushNotificationTranslationForm(PlaceholderModelForm):
    """
    Form for creating and modifying push notification translation objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = PushNotificationTranslation
        #: The fields of the model which should be handled by this form
        fields = ["title", "text", "language"]
