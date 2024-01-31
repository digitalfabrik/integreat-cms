"""
This module contains helpers for the account activation process
(also see :class:`~integreat_cms.cms.views.authentication.account_activation_view.AccountActivationView`).
"""

from __future__ import annotations

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    This token generator is identical to the default password reset token generator of :mod:`django.contrib.auth` with
    the exception of the used HMAC salt.
    This means password reset tokens are no longer accepted for the account activation and vice versa.
    """

    #: The key salt which is passed to the HMAC function
    key_salt = "integreat_cms.cms.utils.account_activation_token_generator.AccountActivationTokenGenerator"


#: The token generator for the account activation process
#: (an instance of :class:`~integreat_cms.cms.utils.account_activation_token_generator.AccountActivationTokenGenerator`)
account_activation_token_generator = AccountActivationTokenGenerator()
