import logging

from django.contrib.auth import get_user_model

from .user_form import UserForm


logger = logging.getLogger(__name__)


class RegionUserForm(UserForm):
    """
    Form for creating and modifying region user objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = get_user_model()
        #: The fields of the model which should be handled by this form
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def __init__(self, data=None, instance=None):

        logger.info(
            "RegionUserForm instantiated with data %s and instance %s", data, instance
        )

        # Instantiate ModelForm
        super().__init__(data=data, instance=instance)

    def save(self, *args, **kwargs):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The saved user object
        :rtype: ~django.contrib.auth.models.User
        """

        logger.info(
            "RegionUserForm saved with cleaned data %s and changed data %s",
            self.cleaned_data,
            self.changed_data,
        )

        # save ModelForm
        return super().save(*args, **kwargs)
