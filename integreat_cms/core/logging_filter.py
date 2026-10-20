import logging

from django.conf import settings


class DebugRequestFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on the current request.

        If REQUEST_DEBUG_USERS is set in the Django settings,
        this filter will only allow log records with level INFO or higher,
        or if the current user's username is in the REQUEST_DEBUG_USERS setting.

        :param record: The log record to filter
        :return: True if the record should be logged, False otherwise
        """
        if settings.REQUEST_DEBUG_USERS:
            from integreat_cms.core.middleware.debug_request import (
                get_request,
            )

            request = get_request()

            if (
                request is not None
                and request.user.username in settings.REQUEST_DEBUG_USERS
            ):
                record.msg = f"Debug User: {request.user.username} - {record.msg}"
                return True
            return record.levelno >= logging.getLevelName(
                getattr(settings, "LOG_LEVEL_NORMAL", "INFO")
            )
        return True


class ApiNotFoundFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Downgrade the log level of "404 Not Found" responses of the API to DEBUG.

        Django logs every 4xx response as WARNING (see :func:`django.utils.log.log_response`).
        Since API clients frequently request non-existing content, these entries clutter the logfile.

        :param record: The log record to filter
        :return: Always True, the record is never dropped
        """
        request = getattr(record, "request", None)
        if (
            getattr(record, "status_code", None) == 404
            and request is not None
            and request.path.startswith("/api/")
        ):
            record.levelno = logging.DEBUG
            record.levelname = logging.getLevelName(logging.DEBUG)
        return True
