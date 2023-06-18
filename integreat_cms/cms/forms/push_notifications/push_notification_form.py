from ...models import PushNotification
from ..custom_model_form import CustomModelForm
from django.forms import CheckboxSelectMultiple


class PushNotificationForm(CustomModelForm):
    """
    Form for creating and modifying push notification objects
    """

    def __init__(self, selected=None, **kwargs):
        r"""
        Initialize push notification form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        # Instantiate CustomModelForm
        super().__init__(**kwargs)

        # Make fields disabled when push notification was already sent
        if self.instance.sent_date:
            self.fields["channel"].disabled = True
            self.fields["regions"].disabled = True
            self.fields["mode"].disabled = True

        if selected is not None:
            self.fields["regions"].initial = selected

    class Meta:
        model = PushNotification
        fields = ["channel", "regions", "mode"]
        widgets = {
            "regions": CheckboxSelectMultiple(),
        }
