import logging
import os
import sys

from urllib.parse import urlparse

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from geopy.geocoders import Nominatim
from geopy.exc import GeopyError

logger = logging.getLogger(__name__)


class CmsConfig(AppConfig):
    """
    This class represents the Django-configuration of the backend.

    See :class:`django.apps.AppConfig` for more information.

    :param name: The name of the app
    :type name: str
    """

    name = "integreat_cms.cms"

    # pylint: disable=unused-import,import-outside-toplevel
    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from .signals import feedback_signals

        # Only check availability if running a server
        if "runserver" in sys.argv or "APACHE_PID_FILE" in os.environ:
            # If Nominatim API is enabled, check availability
            if settings.NOMINATIM_API_ENABLED:
                try:
                    nominatim_url = urlparse(settings.NOMINATIM_API_URL)
                    geolocator = Nominatim(
                        domain=nominatim_url.netloc + nominatim_url.path,
                        scheme=nominatim_url.scheme,
                    )
                    assert geolocator.geocode(
                        "Deutschland",
                        exactly_one=True,
                    )
                    logger.info(
                        "Nominatim API is available at: %r",
                        settings.NOMINATIM_API_URL,
                    )
                except (GeopyError, AssertionError) as e:
                    logger.exception(e)
                    logger.error(
                        "Nominatim API unavailable. You won't be able to "
                        "automatically import location coordinates."
                    )
            else:
                logger.info("Nominatim API is disabled")


authlog = logging.getLogger("auth")


# pylint: disable=unused-argument
@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    r"""
    Log a successful login event

    :param sender: The class of the user that just logged in.
    :type sender: type

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param user: The user instance that just logged in.
    :type user: ~django.contrib.auth.models.User

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict
    """
    ip = request.META.get("REMOTE_ADDR")
    authlog.info("login user=%s, ip=%s", user, ip)


# pylint: disable=unused-argument
@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    r"""
    Log a logout event

    :param sender: The class of the user that just logged out or ``None`` if the user was not authenticated.
    :type sender: type

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param user: The user instance that just logged out or ``None`` if the user was not authenticated.
    :type user: ~django.contrib.auth.models.User

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict
    """
    ip = request.META.get("REMOTE_ADDR")
    authlog.info("logout user=%s, ip=%s", user, ip)


# pylint: disable=unused-argument
@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, request, **kwargs):
    r"""
    Log a failed login event

    :param sender: The name of the module used for authentication.
    :type sender: str

    :param credentials: A dictionary of keyword arguments containing the user credentials that were passed to
                        :func:`~django.contrib.auth.authenticate`. Credentials matching a set of ‘sensitive’ patterns,
                        (including password) will not be sent in the clear as part of the signal.
    :type credentials: dict

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict
    """
    ip = request.META.get("REMOTE_ADDR")
    authlog.warning("login failed user=%s, ip=%s", credentials["username"], ip)
