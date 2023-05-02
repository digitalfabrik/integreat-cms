"""
This module contains helpers for multi-factor-authentication tasks.
"""

import random
import string


def generate_challenge(challenge_len):
    """
    This function generates a random challenge of the given length. It consists of ascii letters and digits.

    Example usage: :class:`~integreat_cms.cms.views.settings.mfa.get_mfa_challenge_view.GetMfaChallengeView`

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


def get_passwordless_mfa_user_id(request):
    """
    Get the user id from the session. This method can be used for the passwordless login, as well as the usual login mode.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: The user id
    :rtype: int
    """
    if "mfa_user_id" in request.session:
        return request.session["mfa_user_id"]
    if "mfa_passwordless_user_id" in request.session:
        return request.session["mfa_passwordless_user_id"]
    return None
