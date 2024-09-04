from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING

from integreat_cms.cms.models.firebase.firebase_statistic import FirebaseStatistic

from ....firebase_api.firebase_data_client import FirebaseDataClient
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command for backing up Firebase Cloud Messaging (FCM) data.
    """

    help: str = "Back up Firebase Cloud Messaging (FCM) data."

    @cached_property
    def client(self) -> FirebaseDataClient:
        """
        Lazy version of the firebase data client because otherwise the documentation build fails.
        """

        return FirebaseDataClient()

    def handle(self, *args: Any, **options: Any) -> None:
        self.set_logging_stream()

        logger.info("Backing up Firebase Cloud Messaging data...")

        statistics = self.client.fetch_notification_statistics()

        for stat in statistics:
            FirebaseStatistic.objects.create(
                date=stat["date"],
                region=stat["region"],
                language_slug=stat["language_slug"],
                count=stat["count"],
            )

        logger.info("Successfully backed up Firebase Cloud Messaging data.")
