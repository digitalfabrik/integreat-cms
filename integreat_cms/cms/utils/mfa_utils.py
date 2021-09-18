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
