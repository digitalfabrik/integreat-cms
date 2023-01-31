import logging

from django.contrib.auth import get_user_model


from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class UserPreferencesForm(CustomModelForm):
    """
    Form for changing a user's preferences
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = get_user_model()
        #: The fields of the model which should be handled by this form
        fields = ["distribute_sidebar_boxes"]
