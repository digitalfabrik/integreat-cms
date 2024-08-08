from django.core.management import call_command
from django_cron import CronJobBase, Schedule


class InactiveUserCleanupJob(CronJobBase):
    """
    A cron job for cleaning up inactive user accounts.
    This job is scheduled to run at a specified interval, as defined by the `RUN_EVERY_MINS` attribute.
    It triggers a Django management command to drop expired user accounts from the database.
    """

    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)

    code = "InactiveUserCleanupJob"

    def do(self) -> None:
        """
        Executes the command to drop expired user accounts.
        """
        call_command("drop_expired_user_accounts")
