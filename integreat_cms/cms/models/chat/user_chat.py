from __future__ import annotations

import time
from typing import TYPE_CHECKING

import requests
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel
from ..languages.language import Language
from ..regions.region import Region
from ...utils.zammad import zammad_request, get_zammad_user_mail

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
        return f"<ABTester (id: {self.id}, device_id: {self.device_id}, is_tester: {self.is_tester})>"

    class Meta:
        verbose_name = _("ab tester")
        verbose_name_plural = _("ab testers")
        ordering = ["-pk"]
        default_permissions = ("delete", "change")


class UserChat(AbstractBaseModel):
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
    most_recent_hits = models.TextField(blank=True)

    # manager for fetching only the newest (i.e. current) chat
    objects = UserChatManager()

    def record_hit(self) -> None:
        """
        Record the timestamp of accesses for ratelimiting purposes
        """
        timestamps = self.most_recent_hits.split(",") if self.most_recent_hits else []
        while len(timestamps) > settings.USER_CHAT_WINDOW_LIMIT:
            timestamps.pop(0)
        self.most_recent_hits = ",".join([*timestamps, str(int(time.time()))])
        self.save()

    def ratelimit_exceeded(self) -> bool:
        """
        Decide if the rate limit for this chat has been exceeded

        :return: if the rate limit has been exceeded
        """
        timestamps = self.most_recent_hits.split(",")
        if len(timestamps) < settings.USER_CHAT_WINDOW_LIMIT:
            return False

        return (
            int(time.time()) - int(timestamps[0])
        ) < 60 * settings.USER_CHAT_WINDOW_MINUTES

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
        return f"<UserChat (id: {self.id}, device_id: {self.device_id}, zammad_id: {self.zammad_id})>"

    def as_dict(self) -> dict[str, Any]:
        """
        API compatible dict representation of the chat
        """
        return {
            "messages": self.messages,
            "ticket_url": f"{self.region.zammad_url}/#ticket/zoom/{self.zammad_id}",
            "evaluation_consent": self.evaluation_consent
        }

    def get_zammad_ticket_messages(self) -> list[dict]:
        """
        Get Zammad ticket articles

        :return: list of Zammad articles (chat messages)
        """
        return zammad_request(
            "GET",
            self.region,
            f"/api/v1/ticket_articles/by_ticket/{self.zammad_id}",
        ).json()

    @cached_property
    def messages(self) -> list[dict]:
        """
        Return all messages stored in Zammad for this ticket

        :return: formatted chat messages
        """
        response = self.get_zammad_ticket_messages()
        keys_to_keep = [
            "status",
            "error",
            "id",
            "body",
            "user_is_author",
            "automatic_answer",
            "evaluation_consent",
        ]
        response = {key: response[key] for key in keys_to_keep if key in response}
        response["content"] = response["body"]
        formatted_messages = []
        for message in response:
            if message["user_is_author"]:
                message["role"] = "user"
            else:
                message["role"] = "agent"
            message["content"] = message["body"]
            formatted_messages.append(message)
        return formatted_messages

    def save_message(self, message: str, internal: bool, automatic_message: bool):
        """
        Add a new message
        """
        del self.messages
        return zammad_request(
            "POST",
            self.region,
            "/api/v1/ticket_articles",
            {
                "ticket_id": self.zammad_id,
                "body": message,
                "internal": internal,
                "automatic_message": automatic_message,
                "content_type": "text/html",
                "type": "web",
                "sender": "Customer" if not automatic_message else "Agent",
            }
        ).status_code == 200

    @cached_property
    def evaluation_consent(self) -> bool:
        """
        Get user evaluation consent
        """
        return zammad_request(
            "GET", self.region, f"/api/v1/tickets/{self.zammad_id}"
        ).json()["evaluation_consent"]

    @evaluation_consent.setter
    def evaluation_consent(self, value: bool) -> None:
        """
        Set user evaluation consent

        :param value: True if user agrees, false if not
        :return
        """
        del self.evaluation_consent
        return zammad_request(
            "POST", self.region, f"/api/v1/tickets/{self.zammad_id}", {"evaluation_consent": value}
        ).status_code == 200

    @cached_property
    def automatic_answers(self) -> bool:
        """
        Check if automatic answers are turned on/off
        """
        return zammad_request(
            "GET", self.region, f"/api/v1/tickets/{self.zammad_id}"
        ).json()["automatic_answers"]

    @automatic_answers.setter
    def automatic_answers(self, value: bool) -> None:
        """
        Turn automatic answers on/off

        :param value: True if user agrees, false if not
        :return
        """
        del self.automatic_answers
        return zammad_request(
            "POST", self.region, f"/api/v1/tickets/{self.zammad_id}", {"automatic_answers": value}
        ).status_code == 200

    def create(self, **kwargs):
        """
        Override super create method to create a Zammad ticket for each new chat
        """
        title = f"[Integreat Chat] [{kwargs.get('language').slug}] {kwargs.get('device_id')}"
        region = kwargs.get('region')
        zammad_id = zammad_request(
            "POST",
            region,
            "/api/v1/",
            {
                "title": title,
                "group": settings.USER_CHAT_TICKET_GROUP,
                "customer": get_zammad_user_mail(region)
            }
        ).json()["ticket_id"]
        return super().create(zammad_id=zammad_id, **kwargs)

    class Meta:
        verbose_name = _("user chat")
        verbose_name_plural = _("user chats")
        ordering = ["-pk"]
        default_permissions = ("delete", "change")
