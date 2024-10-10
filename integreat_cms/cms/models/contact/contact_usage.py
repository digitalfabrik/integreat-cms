from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from .contact import Contact

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class ContactUsage(models.Model):
    """
    Data model representing where a contact is used
    """

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        verbose_name=_("contact"),
        related_name="usages",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    field = models.CharField(max_length=128)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["contact", "content_type", "object_id", "field"],
                name="%(class)s_unique_combination",
            ),
        ]

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Contact object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the contact
        """
        return f"{self.contact.id} ({self.content_object})"

    def __repr__(self) -> str:
        return f"<ContactUsage (id: {self.id}, contact: {self.contact!r}, source: {self.content_object!r})>"
