from ...models import PushNotification
from ..custom_model_form import CustomModelForm
from django.forms import CheckboxSelectMultiple
from django.forms.models import ModelChoiceIteratorValue


class PushNotificationForm(CustomModelForm):
    """
    Form for creating and modifying push notification objects
    """

    def __init__(self, regions=None, selected_regions=None, **kwargs):
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

        if regions is None:
            regions = []
        if selected_regions is None:
            selected_regions = []

        field = self.fields["regions"]
        field.choices = map(lambda obj: (
            ModelChoiceIteratorValue(field.prepare_value(obj), obj),
            field.label_from_instance(obj),
        ), regions)

        self.fields["regions"].initial = selected_regions

    class Meta:
        model = PushNotification
        fields = ["channel", "regions", "mode"]
        widgets = {
            "regions": CheckboxSelectMultiple(),
        }
