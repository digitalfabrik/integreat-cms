import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password,
    password_validators_help_texts,
)
from django.utils.translation import gettext_lazy as _

from ..custom_model_form import CustomModelForm
from ...models import Role
from ...utils.translation_utils import gettext_many_lazy as __
from .organization_field import OrganizationField

logger = logging.getLogger(__name__)


class UserForm(CustomModelForm):
    """
    Form for creating and modifying user objects
    """

    role = forms.ModelChoiceField(
        queryset=Role.objects.filter(staff_role=False),
        required=False,
        label=_("Role"),
        help_text=_("This grants the user all permissions of the selected role"),
    )
    staff_role = forms.ModelChoiceField(
        queryset=Role.objects.filter(staff_role=True),
        required=False,
        label=_("Team"),
        help_text=_("This grants the user all permissions of the selected team"),
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password],
        help_text=password_validators_help_texts,
        required=False,
    )
    send_activation_link = forms.BooleanField(
        initial=True,
        required=False,
        label=_("Send activation link"),
        help_text=__(
            _(
                "Select this option to create an inactive user account and send an activation link per email to the user."
            ),
            _(
                "This link allows the user to choose a password and activates the account after confirmation."
            ),
        ),
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
            "organization",
            "expert_mode",
            "regions",
            "role",
            "send_activation_link",
            "passwordless_authentication_enabled",
        ]
        field_classes = {"organization": OrganizationField}

    def __init__(self, **kwargs):
        r"""
        Initialize user form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """

        # Instantiate CustomModelForm
        super().__init__(**kwargs)

        # check if user instance already exists
        if self.instance.id:
            # set initial role data
            if self.instance.is_staff:
                self.fields["staff_role"].initial = self.instance.role
            else:
                self.fields["role"].initial = self.instance.role
            # don't require password if user already exists
            self.fields["password"].required = False
            # adapt placeholder of password input field
            self.fields["password"].widget.attrs.update(
                {"placeholder": _("Leave empty to keep unchanged")}
            )
        else:
            self.fields["is_active"].initial = False

        # fix labels
        self.fields["password"].label = _("Password")
        if "is_staff" in self.fields:
            self.fields["is_staff"].label = _("Integreat team member")
        self.fields["email"].required = True

        # Check if passwordless authentication is possible for the user
        if (
            "passwordless_authentication_enabled" in self.fields
            and self.instance.totp_key is None
            and not self.instance.mfa_keys.exists()
        ):
            self.fields["passwordless_authentication_enabled"].disabled = True

    def save(self, commit=True):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :type commit: bool

        :return: The saved user object
        :rtype: ~django.contrib.auth.models.User
        """

        # Save CustomModelForm
        user = super().save(commit=commit)

        # check if password field was changed
        if self.cleaned_data["password"]:
            # change password
            user.set_password(self.cleaned_data["password"])
            user.save()

        if user.is_staff:
            role = self.cleaned_data["staff_role"]
        else:
            role = self.cleaned_data["role"]

        for removed_group in user.groups.exclude(id=role.id):
            # Remove unselected roles
            removed_group.user_set.remove(user)
            logger.info(
                "%r was removed from %r",
                removed_group.role,
                user,
            )
        if role.group not in user.groups.all():
            # Assign the selected role
            role.group.user_set.add(user)
            logger.info("%r was assigned to %r", role, user)

        return user

    def clean_email(self):
        """
        Make the email lower case (see :ref:`overriding-modelform-clean-method`)

        :return: The email in lower case
        :rtype: str
        """
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower()
        return email

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()

        if cleaned_data.get("is_superuser") and not cleaned_data.get("is_staff"):
            logger.warning("Superuser %r is not a staff member", self.instance)
            self.add_error(
                "is_superuser",
                forms.ValidationError(
                    _("Only staff members can be superusers"),
                    code="invalid",
                ),
            )

        if cleaned_data.get("is_staff"):
            if cleaned_data.get("role"):
                logger.warning(
                    "Staff member %r can only have staff roles", self.instance
                )
                self.add_error(
                    "staff_role",
                    forms.ValidationError(
                        _("Staff members can only have staff roles"),
                        code="invalid",
                    ),
                )
            if not cleaned_data.get("staff_role"):
                logger.warning("Staff member %r needs a staff role", self.instance)
                self.add_error(
                    "staff_role",
                    forms.ValidationError(
                        _("Staff members have to be member of a team"),
                        code="required",
                    ),
                )
        else:
            if cleaned_data.get("staff_role"):
                logger.warning(
                    "Non-staff member %r cannot have staff roles", self.instance
                )
                self.add_error(
                    "role",
                    forms.ValidationError(
                        _("Only staff members can be member of a team"),
                        code="invalid",
                    ),
                )
            if not cleaned_data.get("role"):
                logger.warning("Non-staff member %r needs a role", self.instance)
                self.add_error(
                    "role",
                    forms.ValidationError(
                        _("Please select a role"),
                        code="required",
                    ),
                )

        if not (
            cleaned_data.get("send_activation_link")
            or cleaned_data.get("password")
            or self.instance
        ):
            self.add_error(
                "send_activation_link",
                forms.ValidationError(
                    _(
                        "Please choose either to send an activation link or set a password."
                    ),
                    code="required",
                ),
            )

        # If this is the global user form, validate the given organization
        # (In the region user form, this is already ensured by the field's choices)
        if "regions" in self.fields and cleaned_data.get("organization"):
            if cleaned_data.get("is_superuser") or cleaned_data.get("is_staff"):
                logger.warning(
                    "Staff member %r cannot be member of an organization", self.instance
                )
                self.add_error(
                    "organization",
                    forms.ValidationError(
                        _("Staff members cannot be member of an organization"),
                        code="invalid",
                    ),
                )
            elif cleaned_data["organization"].region not in cleaned_data.get("regions"):
                logger.warning(
                    "User %r cannot be member of organization %r of other region",
                    self.instance,
                    cleaned_data["organization"],
                )
                self.add_error(
                    "organization",
                    forms.ValidationError(
                        _(
                            "Users can only be members of organizations in regions they have access to"
                        ),
                        code="invalid",
                    ),
                )

        logger.debug("UserForm validated [2] with cleaned data %r", cleaned_data)
        return cleaned_data
