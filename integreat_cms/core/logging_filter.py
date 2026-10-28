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

        Django logs every 4xx response as WARNING (see :func:`django.utils.log.log_response`
        and :meth:`django.core.servers.basehttp.WSGIRequestHandler.log_message`).
        Since API clients frequently request non-existing content, these entries clutter the logfile.

        The logger level is only checked before filters are applied, so downgraded records
        have to be dropped here if the logger is not enabled for DEBUG.

        :param record: The log record to filter
        :return: False if the record was downgraded and DEBUG is not enabled, True otherwise
        """
        if getattr(record, "status_code", None) == 404 and self.get_path(
            record
        ).startswith("/api/"):
            record.levelno = logging.DEBUG
            record.levelname = logging.getLevelName(logging.DEBUG)
            return logging.getLogger(record.name).isEnabledFor(logging.DEBUG)
        return True

    @staticmethod
    def get_path(record: logging.LogRecord) -> str:
        """
        Get the requested path of a log record of the ``django.request`` or ``django.server`` logger.

        :param record: The log record
        :return: The requested path or an empty string if it cannot be determined
        """
        # Records of "django.request" contain the HttpRequest object
        if path := getattr(getattr(record, "request", None), "path", None):
            return path
        # Records of "django.server" contain the request line (e.g. "GET /api/v3/ HTTP/1.1") as first argument
        if isinstance(record.args, tuple) and record.args:
            request_line = str(record.args[0]).split()
            if len(request_line) > 1:
                return request_line[1]
        return ""
