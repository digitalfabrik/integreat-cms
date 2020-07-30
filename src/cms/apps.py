import logging
import sys

from django.conf import settings
from django.apps import AppConfig
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class CmsConfig(AppConfig):
    """
    This class represents the Django-configuration of the backend.

    See :class:`django.apps.AppConfig` for more information.

    :param name: The name of the app
    :type name: str
    """

    name = "cms"

    def ready(self):
        """
        This function gets executed exactly once each time the cms starts. We use it to check wether the secret key was
        not changed in production mode and show an error message if this is the case.

        See :meth:`django.apps.AppConfig.ready` for more information.
        """
        if (
            settings.SECRET_KEY == "-!v282$zj815_q@htaxcubylo)(l%a+k*-xi78hw*#s2@i86@_"
            and not settings.DEBUG
        ):
            logger.error(
                "You are running the Integreat CMS in production mode. Change the SECRET_KEY in the settings.py!"
            )
            sys.exit(1)


authlog = logging.getLogger("auth")


@receiver(user_logged_in)
def user_logged_in_callback(
    sender, request, user, **kwargs
):  # pylint: disable=unused-argument
    ip = request.META.get("REMOTE_ADDR")
    authlog.info("login user=%s, ip=%s", user, ip)


@receiver(user_logged_out)
def user_logged_out_callback(
    sender, request, user, **kwargs
):  # pylint: disable=unused-argument
    ip = request.META.get("REMOTE_ADDR")
    authlog.info("logout user=%s, ip=%s", user, ip)


@receiver(user_login_failed)
def user_login_failed_callback(
    sender, credentials, request, **kwargs
):  # pylint: disable=unused-argument
    ip = request.META.get("REMOTE_ADDR")
    authlog.warning("login failed user=%s, ip=%s", credentials["username"], ip)
