from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cacheops import invalidate_model

from ....cms.models import Event, EventTranslation, ExternalCalendar
from ....cms.utils.external_calendar_utils import import_events
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to import events from external calendars
    """

    help: str = "Import events from external calendars"

    def handle(self, *args: Any, **options: Any) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param \**options: The supplied keyword options
        """
        self.set_logging_stream()
        calendars = ExternalCalendar.objects.all()
        for calendar in calendars:
            import_events(calendar, logger)

        invalidate_model(Event)
        invalidate_model(EventTranslation)
        invalidate_model(ExternalCalendar)
