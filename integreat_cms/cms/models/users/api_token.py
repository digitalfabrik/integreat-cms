from __future__ import annotations

import hashlib
import secrets
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel

if TYPE_CHECKING:
    from typing import Self

    from .user import User

#: Number of random bytes used for the secret part of a token
TOKEN_SECRET_BYTES: int = 32

#: Number of random bytes used for the prefix which identifies a token
TOKEN_PREFIX_BYTES: int = 6


def hash_token(token: str) -> str:
    """
    Hash a token for storage in the database

    Tokens are generated with enough entropy to make brute-forcing infeasible, so a plain
    SHA-256 digest is sufficient here — a slow password hash would only add latency to every
    single API request without adding practical security.

    :param token: The plaintext token
    :return: The hex digest of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


class ApiToken(AbstractBaseModel):
    """
    Data model representing a personal API token of a user

    The token authenticates API requests on behalf of its user, so requests inherit exactly the
    permissions of that user and the RBAC structure is not bypassed. Only a hash of the token is
    stored — the plaintext is shown to the user once directly after creation and cannot be
    recovered afterwards.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_tokens",
        verbose_name=_("user"),
    )
    name = models.CharField(max_length=200, verbose_name=_("token name"))
    prefix = models.CharField(
        max_length=16,
        unique=True,
        verbose_name=_("token prefix"),
        help_text=_("The public part of the token which is used to identify it."),
    )
    token_hash = models.CharField(
        max_length=64,
        verbose_name=_("token hash"),
        help_text=_("The hash of the full token."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )
    last_usage = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("last date of use"),
    )

    @classmethod
    def create_token(cls, user: User, name: str) -> tuple[Self, str]:
        """
        Create a new API token for the given user

        :param user: The user the token belongs to
        :param name: The name of the token
        :return: A tuple of the created token object and the plaintext token
        """
        prefix = secrets.token_hex(TOKEN_PREFIX_BYTES)
        secret = secrets.token_urlsafe(TOKEN_SECRET_BYTES)
        plaintext = f"{prefix}.{secret}"
        token = cls.objects.create(
            user=user,
            name=name,
            prefix=prefix,
            token_hash=hash_token(plaintext),
        )
        return token, plaintext

    @classmethod
    def get_by_token(cls, plaintext: str) -> Self | None:
        """
        Look up a token object by its plaintext representation

        The candidate row is looked up by its public prefix rather than by the hash itself, so that
        the database never runs an equality comparison on the secret value. The single comparison
        of the hash is then done in constant time.

        :param plaintext: The plaintext token as sent by the client
        :return: The matching token object, or ``None`` if the token is unknown
        """
        prefix, separator, _secret = plaintext.partition(".")
        if not separator:
            return None
        if not (token := cls.objects.filter(prefix=prefix).first()):
            return None
        if not secrets.compare_digest(token.token_hash, hash_token(plaintext)):
            return None
        return token

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which
        would return ``ApiToken object (id)``. It is used in the Django admin backend and as
        label for ModelChoiceFields.

        :return: A readable string representation of the API token
        """
        return f"{self.name} ({self.user.full_user_name})"

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return
        ``<ApiToken: ApiToken object (id)>``. It is used for logging.

        :return: The canonical string representation of the API token
        """
        class_name = type(self).__name__
        if not self.pk:
            return f"<{class_name} (unsaved instance)>"
        return f"<{class_name} (id: {self.id}, name: {self.name}, user: {self.user.username})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("API token")
        #: The plural verbose name of the model
        verbose_name_plural = _("API tokens")
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
