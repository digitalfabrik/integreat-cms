from __future__ import annotations

import hashlib
import secrets
from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel

if TYPE_CHECKING:
    from typing import Any


def generate_random_hash() -> str:
    """
    Generate a random hash. Produces output of length 64.

    :return: The generated random hash
    """
    return hashlib.sha256(secrets.token_bytes(512)).hexdigest()


class AttachmentMap(AbstractBaseModel):
    """
    A model for a mapping a random hash to a Zammad attachment ID
    """

    user_chat = models.ForeignKey(
        "cms.UserChat", on_delete=models.CASCADE, related_name="attachments"
    )
    random_hash = models.CharField(
        max_length=64, default=generate_random_hash, unique=True
    )
    article_id = models.IntegerField()
    attachment_id = models.IntegerField()
    mime_type = models.CharField(max_length=32)

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``AttachmentMap object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the attachment map
        """
        return f"({self.pk}, {self.random_hash}) -> {self.attachment_id}"

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<AttachmentMap: AttachmentMap object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the attachment map
        """
        return f"<AttachmentMap (id: {self.id}, random_hash: {self.random_hash}, attachment_id: {self.attachment_id})>"

    class Meta:
        verbose_name = _("attachment map")
        verbose_name_plural = _("attachment maps")
        ordering = ["-pk"]
        default_permissions = ("delete", "change")
