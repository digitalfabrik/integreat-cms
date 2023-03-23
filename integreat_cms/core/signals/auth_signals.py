"""
This module contains signal handlers related to authentication.
"""

import logging

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

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
