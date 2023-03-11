import logging
import os
import sys

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    """
    This class represents the Django-configuration of the backend.

    See :class:`django.apps.AppConfig` for more information.

    :param name: The name of the app
    :type name: str
    """

    #: Full Python path to the application
    name = "integreat_cms.core"
    #: Human-readable name for the application
    verbose_name = _("Core")

    #: Whether the availability of external APIs should be checked
    test_external_apis = False

    def ready(self):
        # pylint: disable=unused-import,import-outside-toplevel
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals

        # Determine whether the availability of external APIs should be checked
        self.test_external_apis = (
            # Either the dev server is started with the "runserver" command,
            # but it's not the main process (to ignore autoreloads)
            ("runserver" in sys.argv and "RUN_MAIN" not in os.environ)
            # or the prod server is started via wsgi
            or "APACHE_PID_FILE" in os.environ
        )
