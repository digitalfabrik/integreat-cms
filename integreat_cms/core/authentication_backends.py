"""
This file contains custom authentication backends, see :ref:`ref/contrib/auth:authentication backends` and
:ref:`django:authentication-backends`.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend


UserModel = get_user_model()


class EmailAuthenticationBackend(BaseBackend):
    """
    This authentication backend allows users to login with their email address instead of their username
    """

    def authenticate(self, request, **kwargs):
        r"""
        Try to authenticate a user with the given email and password

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: Either the authenticated user or ``None`` is the credentials were not valid
        :rtype: ~integreat_cms.cms.models.users.user.User
        """
        email = kwargs.get(UserModel.USERNAME_FIELD)
        if not email:
            return None
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

    def get_user(self, user_id):
        """
        Get the user by its primary key

        :param user_id: The id of the user
        :type user_id: int

        :return: Either the user or ``None`` if no user with this id exists
        :rtype: ~integreat_cms.cms.models.users.user.User
        """
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
