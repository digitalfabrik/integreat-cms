from ..custom_model_form import CustomModelForm
from ...models import PushNotification


class PushNotificationForm(CustomModelForm):
    """
    Form for creating and modifying push notification objects
    """

    def __init__(self, **kwargs):
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
            self.fields["mode"].disabled = True

    class Meta:
        model = PushNotification
        fields = ["channel", "mode"]
