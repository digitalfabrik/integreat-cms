from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError
from django.utils import timezone

from ....cms.models import PushNotification, Region
from ....firebase_api.firebase_api_client import FirebaseApiClient
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any


logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to send timed push notifications
    """

    help: str = "Send pending push notifications"

    def handle(self, *args: Any, **options: Any) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param \**options: The supplied keyword options
        """
        self.set_logging_stream()

        if not settings.FCM_ENABLED:
            raise CommandError("Push notifications are disabled")

        if settings.DEBUG:
            try:
                Region.objects.get(slug=settings.TEST_REGION_SLUG)
                logger.debug(
                    "The system runs with DEBUG=True, so notifications will only be sent to the test region (%s).",
                    settings.TEST_REGION_SLUG,
                )
            except Region.DoesNotExist as e:
                raise CommandError(
                    f"The system runs with DEBUG=True but the region with TEST_REGION_SLUG={settings.TEST_REGION_SLUG} does not exist."
                ) from e

        pending_push_notifications = PushNotification.objects.filter(
            scheduled_send_date__isnull=False,
            sent_date__isnull=True,
            draft=False,
            scheduled_send_date__lte=timezone.now(),
            scheduled_send_date__gte=timezone.now()
            - timedelta(hours=settings.FCM_NOTIFICATION_RETAIN_TIME_IN_HOURS),
        )
        if total := len(pending_push_notifications):
            for counter, push_notification in enumerate(pending_push_notifications):
                self.send_push_notification(counter, total, push_notification)
            logger.success(  # type: ignore[attr-defined]
                "✔ All %d scheduled push notifications have been processed.",
                total,
            )
        else:
            logger.info(
                "There are currently no push notifications scheduled to be sent."
            )

    def send_push_notification(
        self, counter: int, total: int, push_notification: PushNotification
    ) -> None:
        """
        Sends a push notification

        :param counter: The current counter
        :param total: How many push notifications are scheduled for this slot
        :param push_notification: The push notification object
        """
        try:
            push_sender = FirebaseApiClient(push_notification)
            if not push_sender.is_valid():
                logger.error(
                    "Push notification %d/%d %r cannot be sent because required texts are missing",
                    counter,
                    total,
                    push_notification,
                )
            elif push_sender.send_all():
                logger.success(  # type: ignore[attr-defined]
                    "Successfully sent %d/%d %r",
                    counter,
                    total,
                    push_notification,
                )
                push_notification.sent_date = timezone.now()
                push_notification.save()
            else:
                logger.error(
                    "Push notification %d/%d %r could not be sent",
                    counter,
                    total,
                    push_notification,
                )
        except ImproperlyConfigured as e:
            logger.error(
                "Push notification %d/%d %r could not be sent due to a configuration error: %s",
                counter,
                total,
                push_notification,
                e,
            )
