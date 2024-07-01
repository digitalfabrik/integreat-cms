from __future__ import annotations

import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel

if TYPE_CHECKING:
    from typing import Any


# pylint: disable=too-few-public-methods
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
    zammad_id = models.IntegerField()
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
        self.most_recent_hits = ",".join(timestamps + [str(int(time.time()))])
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

    class Meta:
        verbose_name = _("user chat")
        verbose_name_plural = _("user chats")
        ordering = ["-pk"]
        default_permissions = ("delete", "change")
