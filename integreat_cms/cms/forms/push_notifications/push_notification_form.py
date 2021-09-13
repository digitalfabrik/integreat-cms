from ..custom_model_form import CustomModelForm
from ...models import PushNotification


class PushNotificationForm(CustomModelForm):
    """
    Form for creating and modifying push notification objects
    """

    class Meta:
        model = PushNotification
        fields = ["channel", "mode"]
