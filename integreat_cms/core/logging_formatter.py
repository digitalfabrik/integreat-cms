import logging


class ColorFormatter(logging.Formatter):
    """
    Logging Formatter to add colors
    """

    #: The bash color codes for the different logging levels
    COLORS = {
        logging.DEBUG: 36,  # cyan
        logging.INFO: 34,  # blue
        logging.WARNING: 33,  # yellow
        logging.ERROR: 31,  # red
        logging.CRITICAL: 31,  # red
    }

    def format(self, record):
        """
        Format the specified record as colored text (see :meth:`python:logging.Formatter.format`).

        :param record: The log record
        :type record: ~logging.LogRecord

        :return: The formatted logging message
        :rtype: str
        """
        # Define color escape sequence
        color = f"\x1b[0;{self.COLORS.get(record.levelno)}m"
        # Make level name bold
        fmt = self._fmt.replace("{levelname}", "\x1b[1m{levelname}" + color)
        # Make entire line colored
        # pylint: disable=protected-access
        self._style._fmt = color + fmt + "\x1b[0m"
        return super().format(record)


class RequestFormatter(logging.Formatter):
    """
    Logging Formatter to log the GET parameters of a failed HTTP request
    """

    def format(self, record):
        """
        Format the specified record including the request if possible (see :meth:`python:logging.Formatter.format`).

        :param record: The log record
        :type record: ~logging.LogRecord

        :return: The formatted logging message
        :rtype: str
        """
        message = super().format(record)
        # Check whether this record belongs to a request
        if record.name == "django.request":
            # Prepend HTTP status code to the message
            message = message.replace(
                "django.request - ", f"django.request - {record.status_code} "
            )
            # Append the GET query string to the message
            if query := record.request.META["QUERY_STRING"]:
                if "\n" in message:
                    # If the string is multi-line (e.g. because the traceback follows), only append to first line
                    message = message.replace("\n", f"?{query}\n", 1)
                else:
                    # If the string consists of one single line, just append it to the end
                    message += f"?{query}"
        return message
