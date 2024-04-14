"""
This module contains signal handlers related to authentication.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.base import ModelBase
    from django.http import HttpRequest

    from integreat_cms.cms.models.users.user import User

authlog = logging.getLogger("auth")


# pylint: disable=unused-argument
@receiver(user_logged_in)
def user_logged_in_callback(
    sender: ModelBase,
    request: HttpRequest,
    user: User,
    **kwargs: Any,
) -> None:
    r"""
    Log a successful login event

    :param sender: The class of the user that just logged in.
    :param request: The current request
    :param user: The user instance that just logged in.
    :param \**kwargs: The supplied keyword arguments
    """
    ip = request.META.get("REMOTE_ADDR")
    authlog.info("login user=%s, ip=%s", user, ip)


# pylint: disable=unused-argument
@receiver(user_logged_out)
def user_logged_out_callback(
    sender: ModelBase, request: HttpRequest, user: User, **kwargs: Any
) -> None:
    r"""
    Log a logout event

    :param sender: The class of the user that just logged out or ``None`` if the user was not authenticated.
    :param request: The current request
    :param user: The user instance that just logged out or ``None`` if the user was not authenticated.
    :param \**kwargs: The supplied keyword arguments
    """
    ip = request.META.get("REMOTE_ADDR")
    authlog.info("logout user=%s, ip=%s", user, ip)


# pylint: disable=unused-argument
@receiver(user_login_failed)
def user_login_failed_callback(
    sender: ModelBase, credentials: dict[str, str], request: HttpRequest, **kwargs: Any
) -> None:
    r"""
    Log a failed login event

    :param sender: The name of the module used for authentication.
    :param credentials: A dictionary of keyword arguments containing the user credentials that were passed to
                        :func:`~django.contrib.auth.authenticate`. Credentials matching a set of ‘sensitive’ patterns,
                        (including password) will not be sent in the clear as part of the signal.
    :param request: The current request
    :param \**kwargs: The supplied keyword arguments
    """
    ip = request.META.get("REMOTE_ADDR")
    authlog.warning("login failed user=%s, ip=%s", credentials["username"], ip)
