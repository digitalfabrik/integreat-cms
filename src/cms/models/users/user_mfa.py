from django.db import models
from django.conf import settings


class UserMfa(models.Model):
    """
    Data model representing a user's multi-factor-authentication (MFA) key

    :param id: The database id of the mfa key
    :param key_id: The webauthn id of the mfa key
    :param name: The name of the mfa key
    :param public_key: The mfa public key
    :param sign_count: Token to prevent replay attacks
    :param created_at: The date and time when the mfa key was created
    :param last_usage: The date and time when the mfa key was last used

    Relationship fields:

    :param user: The user this key belongs to (related name: ``mfa_keys``)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="mfa_keys", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    key_id = models.BinaryField(max_length=255, null=False)
    public_key = models.BinaryField(max_length=255, null=False)
    sign_count = models.IntegerField(null=False)
    last_usage = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + str(self.key_id)

    class Meta:
        default_permissions = ()
        unique_together = (
            (
                "user",
                "name",
            ),
        )
