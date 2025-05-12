from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

from ...utils.zammad import ZammadAPI
from ..abstract_base_model import AbstractBaseModel
from ..languages.language import Language
from ..regions.region import Region

if TYPE_CHECKING:
    from typing import Any


class UserChatManager(models.Manager):
    """
    custom manager providing function to get the current chat
    """

    def current_chat(self, device_id: str, **kwargs: Any) -> UserChat:
        r"""
        Return only the newest (i.e. current) chat for a given device_id

        :param device_id: the device id for which we want the current chat
        :param \**kwargs: The supplied kwargs
        :return: the current chat for the given device_id
        """
        return (
            self.get_queryset()
            .filter(device_id=device_id, **kwargs)
            .order_by("-pk")
            .first()
        )

    def create(self, region: Region, device_id: str, language: Language) -> UserChat:
        """
        Override super create method to create a Zammad ticket for each new chat

        :param region: Region to which the chat belongs
        :param device_id: UUID identifying a chat/device
        :param language: the UI language of the app
        """
        chat = UserChat(region=region, device_id=device_id, language=language)
        title = f"[Integreat Chat] [{language.slug}] {device_id}"
        chat.zammad_id = chat.create_ticket(title)
        chat.save()
        return chat


class ABTester(AbstractBaseModel):
    """
    A helper model for keeping track of A/B testers for the chat feature
    """

    device_id = models.CharField(max_length=200)
    region = models.ForeignKey("cms.Region", on_delete=models.CASCADE)
    is_tester = models.BooleanField(default=False)

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``ABTester object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the ab tester
        """
        return f"({self.pk}, {self.device_id}) is tester: {self.is_tester}"

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<ABTester: ABTester object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the ab tester
        """
        return f"<ABTester (id: {self.pk}, device_id: {self.device_id}, is_tester: {self.is_tester})>"

    class Meta:
        verbose_name = _("ab tester")
        verbose_name_plural = _("ab testers")
        ordering = ["-pk"]
        default_permissions = ("delete", "change")


class UserChat(AbstractBaseModel, ZammadAPI):
    """
    A model for a user (app) chat, mapping a device ID to a Zammad ticket ID
    """

    device_id = models.CharField(max_length=200)
    zammad_id = models.IntegerField()  # Zammad ticket id
    region = models.ForeignKey(
        Region,
        null=True,
        on_delete=models.CASCADE,
        related_name="chats",
        verbose_name="Region for Chat",
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="chats",
        verbose_name="Language of chat app user",
    )

    # manager for fetching only the newest (i.e. current) chat
    objects = UserChatManager()

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``UserChat object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the user chat
        """
        return f"({self.pk}, {self.device_id}) -> {self.zammad_id}"

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<UserChat: UserChat object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the user chat
        """
        return f"<UserChat (id: {self.pk}, device_id: {self.device_id}, zammad_id: {self.zammad_id})>"

    def as_dict(self) -> dict[str, Any]:
        """
        API compatible dict representation of the chat
        """
        response = {
            "messages": list(self.get_messages()),
            "evaluation_consent": bool(self.evaluation_consent),
            "chatbot_typing": bool(self.processing_answer),
        }
        if self.region is not None:
            response["ticket_url"] = (
                f"{self.region.zammad_url}/#ticket/zoom/{self.zammad_id}"
            )
        return response

    class Meta:
        verbose_name = _("user chat")
        verbose_name_plural = _("user chats")
        ordering = ["-pk"]
        default_permissions = ("delete", "change")
