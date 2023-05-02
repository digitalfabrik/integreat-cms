"""
This module contains helpers for multi-factor-authentication tasks.
"""

import random
import string

from django.contrib.auth import get_user_model


def generate_challenge(challenge_len):
    """
    This function generates a random challenge of the given length. It consists of ascii letters and digits.

    Example usage: :class:`~integreat_cms.cms.views.settings.webauthn.get_mfa_challenge_view.GetMfaChallengeView`

    :param challenge_len: The desired length of the challenge
    :type challenge_len: int

    :return: A random string of the requested length
    :rtype: str
    """
    return "".join(
        [
            random.SystemRandom().choice(string.ascii_letters + string.digits)
            for i in range(challenge_len)
        ]
    )


def get_mfa_user(request):
    """
    Get the user from the session if it exists. This method can be used for the passwordless login, as well as the usual login mode.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: The user
    :rtype: ~integreat_cms.cms.models.users.user.User
    """
    if "mfa_user_id" in request.session:
        user = get_user_model().objects.get(id=request.session["mfa_user_id"])
        return user
    return None
