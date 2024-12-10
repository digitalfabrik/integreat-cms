from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.utils import timezone

from ....cms.models import User
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to delete users who were not activated within 7 days of creation
    """

    help: str = (
        "Deletes users who were not activated within 7 days of their account creation."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        self.set_logging_stream()

        # Define the cutoff date: 7 days ago from now
        cutoff_date = timezone.now() - timedelta(days=7)

        # Fetch users who have not been activated and whose creation date is before the cutoff date
        users_to_delete = User.objects.filter(
            is_active=False,
            date_joined__lte=cutoff_date,
        )

        num_users_to_delete = users_to_delete.count()

        if not num_users_to_delete:
            logger.info("No inactive users were found who need to be deleted.")
            return

        logger.info("Found %d inactive users to delete.", num_users_to_delete)

        # Delete the users
        users_to_delete.delete()

        logger.info(
            "Successfully deleted %d inactive users who were not activated within 7 days.",
            num_users_to_delete,
        )
