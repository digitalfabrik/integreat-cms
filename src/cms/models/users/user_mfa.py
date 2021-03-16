from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class UserMfa(models.Model):
    """
    Data model representing a user's multi-factor-authentication (MFA) key
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mfa_keys",
        verbose_name=_("user"),
    )
    name = models.CharField(max_length=200, verbose_name=_("name"))
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
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``UserMfa object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the user MFA
        :rtype: str
        """
        return f"{self.name} ({self.user.profile.full_user_name})"

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<UserMfa: UserMfa object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the user MFA
        :rtype: str
        """
        return (
            f"<UserMfa (id: {self.id}, name: {self.name}, user: {self.user.username})>"
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("multi-factor authentication key")
        #: The plural verbose name of the model
        verbose_name_plural = _("multi-factor authentication keys")
        #: The default permissions for this model
        default_permissions = ()
        unique_together = (
            (
                "user",
                "name",
            ),
        )
