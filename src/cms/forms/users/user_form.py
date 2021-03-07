import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as Role
from django.contrib.auth.password_validation import (
    validate_password,
    password_validators_help_texts,
)
from django.utils.translation import ugettext_lazy as _


from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class UserForm(CustomModelForm):
    """
    Form for creating and modifying user objects
    """

    roles = forms.ModelMultipleChoiceField(queryset=Role.objects.all(), required=False)
    password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password],
        help_text=password_validators_help_texts,
    )

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = get_user_model()
        #: The fields of the model which should be handled by this form
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
            "is_superuser",
        ]

    def __init__(self, data=None, instance=None):

        logger.info(
            "UserForm instantiated with data %s and instance %s", data, instance
        )

        # instantiate ModelForm
        super().__init__(data=data, instance=instance)

        # check if user instance already exists
        if self.instance.id:
            # set initial role data
            self.fields["roles"].initial = self.instance.groups.all()
            # don't require password if user already exists
            self.fields["password"].required = False
            # adapt placeholder of password input field
            self.fields["password"].widget.attrs.update(
                {"placeholder": _("Leave empty to keep unchanged")}
            )
        # fix password label
        self.fields["password"].label = _("Password")

    # pylint: disable=signature-differs
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
            "UserForm saved with cleaned data %s and changed data %s",
            self.cleaned_data,
            self.changed_data,
        )

        # save ModelForm
        user = super().save(*args, **kwargs)

        # check if password field was changed
        if self.cleaned_data["password"]:
            # change password
            user.set_password(self.cleaned_data["password"])
            user.save()

        # assign all selected roles which the user does not have already
        for role in set(self.cleaned_data["roles"]) - set(user.groups.all()):
            role.user_set.add(user)
            logger.info("The role %s was assigned to the user %s", role, user)

        # remove all unselected roles which the user had before
        for role in set(user.groups.all()) - set(self.cleaned_data["roles"]):
            role.user_set.remove(user)
            logger.info("The role %s was removed from the user %s", role, user)

        return user
