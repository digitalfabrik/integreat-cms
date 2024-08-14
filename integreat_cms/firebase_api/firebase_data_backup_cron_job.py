import logging
from functools import cached_property

from django_cron import CronJobBase, Schedule

from integreat_cms.firebase_api.firebase_data_client import FirebaseDataClient
from integreat_cms.firebase_api.firebase_statistic import FirebaseStatistic


class FirebaseDataBackupCronJob(CronJobBase):
    """
    A cron job for backing up Firebase Cloud Messaging (FCM) data.

    This job is scheduled to run at a specified time daily, as defined by the `RUN_AT_TIMES` attribute.
    It retrieves notification statistics from Firebase and updates or creates records in the database
    for each region and language combination.
    """

    RUN_AT_TIMES = ["04:00"]

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = "integreat_cms.firebase_data_backup_cron_job"

    logger = logging.getLogger(__name__)

    @cached_property
    def client(self) -> FirebaseDataClient:
        """
        Lazy version of the firebase data client because otherwise the documentation build fails.
        """

        return FirebaseDataClient()

    def do(self) -> None:
        """
        Executes the cron job to back up Firebase Cloud Messaging data.
        """

        self.logger.info("Backing up Firebase Cloud Messaging data...")

        statistics = self.client.fetch_notification_statistics()

        for region, region_data in statistics.items():
            languages_data = region_data.get("languages", {})
            if isinstance(languages_data, dict):
                for language, average_count in languages_data.items():
                    FirebaseStatistic.objects.update_or_create(
                        region=region,
                        language_slug=language,
                        date=region_data["date"],
                        defaults={"count": average_count},
                    )

        self.logger.info("Successfully backed up Firebase Cloud Messaging data.")
