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

#: The separator between the prefix and the secret part of a token
TOKEN_SEPARATOR: str = "."  # noqa: S105

#: Number of bytes of the token hash (determined by the hash algorithm, not by the token length)
TOKEN_HASH_BYTES: int = hashlib.sha256().digest_size


def _hash_token(prefix: bytes, secret: str) -> bytes:
    """
    Hash a token for storage in and lookup from the database

    The plaintext token is assembled from its two parts here instead of being passed in as a whole,
    so that the same format is guaranteed for storage and lookup.

    Tokens are generated with enough entropy to make brute-forcing infeasible, so a plain
    SHA-256 digest is sufficient here — a slow password hash would only add latency to every
    single API request without adding practical security.

    :param prefix: The public prefix of the token
    :param secret: The secret part of the token
    :return: The raw digest of the full token
    """
    plaintext = f"{prefix.hex()}{TOKEN_SEPARATOR}{secret}"
    return hashlib.sha256(plaintext.encode()).digest()


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
    prefix = models.BinaryField(
        max_length=TOKEN_PREFIX_BYTES,
        unique=True,
        verbose_name=_("token prefix"),
        help_text=_(
            "The public part of the token which is used to identify it. It is stored as raw bytes "
            "and hex encoded in the plaintext token."
        ),
    )
    token_hash = models.BinaryField(
        max_length=TOKEN_HASH_BYTES,
        verbose_name=_("token hash"),
        help_text=_(
            "The raw SHA-256 digest of the full plaintext token, i.e. of the hex encoded prefix, "
            "the separator and the secret."
        ),
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
        prefix = secrets.token_bytes(TOKEN_PREFIX_BYTES)
        secret = secrets.token_urlsafe(TOKEN_SECRET_BYTES)
        token = cls.objects.create(
            user=user,
            name=name,
            prefix=prefix,
            token_hash=_hash_token(prefix, secret),
        )
        return token, f"{prefix.hex()}{TOKEN_SEPARATOR}{secret}"

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
        prefix_hex, separator, secret = plaintext.partition(TOKEN_SEPARATOR)
        if not separator or len(prefix_hex) != TOKEN_PREFIX_BYTES * 2:
            return None
        try:
            prefix = bytes.fromhex(prefix_hex)
        except ValueError:
            return None
        if not (token := cls.objects.filter(prefix=prefix).first()):
            return None
        if not secrets.compare_digest(token.token_hash, _hash_token(prefix, secret)):
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
