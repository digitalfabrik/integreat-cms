from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError
from django.utils import timezone

from ....cms.models import PushNotification, Region
from ....firebase_api.firebase_api_client import FirebaseApiClient
from ..log_command import LogCommand


class Command(LogCommand):
    """
    Management command to send timed push notifications
    """

    help = "Send pending push notifications"

    def handle(self, *args, **options):
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**options: The supplied keyword options
        :type \**options: dict
        """
        if not settings.FCM_ENABLED:
            raise CommandError("Push notifications are disabled")

        if settings.DEBUG:
            try:
                Region.objects.get(slug=settings.TEST_REGION_SLUG)
                self.print_info(
                    f"The system runs with DEBUG=True, so notifications will only be sent to the test region ({settings.TEST_REGION_SLUG})!"
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
        )
        for pn in pending_push_notifications:
            self.send_push_notification(pn)
        self.print_success("Done!")

    def send_push_notification(self, pn):
        """
        Sends a push notification

        :param pn: The push notification object
        :type pn: ~integreat_cms.cms.models.push_notifications.push_notification.PushNotification
        """
        try:
            push_sender = FirebaseApiClient(pn)
            if not push_sender.is_valid():
                self.print_error(
                    f"Push notification {repr(pn)} cannot be sent because required texts are missing"
                )
            elif push_sender.send_all():
                self.print_info(f"Successfully sent {repr(pn)}")
                pn.sent_date = timezone.now()
                pn.save()
            else:
                self.print_error(f"Push notification {repr(pn)} could not be sent")
        except ImproperlyConfigured as e:
            self.print_error(
                f"Push notification {repr(pn)} could not be sent due to a configuration error: {e}"
            )
