"""
This file contains custom authentication backends, see :ref:`ref/contrib/auth:authentication backends` and
:ref:`django:authentication-backends`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

    from integreat_cms.cms.models.users.user import User

UserModel = get_user_model()


class EmailAuthenticationBackend(BaseBackend):
    """
    This authentication backend allows users to login with their email address instead of their username
    """

    def authenticate(self, request: HttpRequest, **kwargs: Any) -> User | None:
        r"""
        Try to authenticate a user with the given email and password

        :param request: The current request
        :param \**kwargs: The supplied keyword arguments
        :return: Either the authenticated user or ``None`` is the credentials were not valid
        """
        if email := kwargs.get(UserModel.USERNAME_FIELD):
            password = kwargs.get("password")
            try:
                user = UserModel.objects.get(**{UserModel.EMAIL_FIELD: email.lower()})
            except UserModel.DoesNotExist:
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a nonexistent user (#20760).
                UserModel().set_password(password)
            else:
                if user.check_password(password) and user.is_active:
                    return user
        return None

    def get_user(self, user_id: int) -> User | None:
        """
        Get the user by its primary key

        :param user_id: The id of the user
        :return: Either the user or ``None`` if no user with this id exists
        """
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
