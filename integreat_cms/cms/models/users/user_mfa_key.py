from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel


class UserMfaKey(AbstractBaseModel):
    """
    Data model representing a user's multi-factor-authentication (MFA) key
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mfa_keys",
        verbose_name=_("user"),
    )
    name = models.CharField(max_length=200, verbose_name=_("key name"))
    key_id = models.BinaryField(
        max_length=255, null=False, verbose_name=_("WebAuthn ID")
    )
    public_key = models.BinaryField(
        max_length=255,
        null=False,
        verbose_name=_("multi-factor-authentication public key"),
    )
    sign_count = models.IntegerField(
        null=False,
        verbose_name=_("sign count"),
        help_text=_("Token to prevent replay attacks."),
    )
    last_usage = models.DateTimeField(
        null=True,
        verbose_name=_("last date of use"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``UserMfaKey object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the user MFA
        :rtype: str
        """
        return f"{self.name} ({self.user.full_user_name})"

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<UserMfaKey: UserMfaKey object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the user MFA
        :rtype: str
        """
        return f"<UserMfaKey (id: {self.id}, name: {self.name}, user: {self.user.username})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("multi-factor authentication key")
        #: The plural verbose name of the model
        verbose_name_plural = _("multi-factor authentication keys")
        #: The default permissions for this model
        default_permissions = ()
        #: Sets of field names that, taken together, must be unique:
        unique_together = (
            (
                "user",
                "name",
            ),
        )
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["name"]
