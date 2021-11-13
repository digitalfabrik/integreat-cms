"""
This package contains views related to the multi-factor-authentication login.

The 2FA login process is as follows:

1. User tries to login with the :class:`~integreat_cms.cms.views.authentication.login_view.LoginView`
2. If the user has at least one :class:`~integreat_cms.cms.models.users.user_mfa_key.UserMfaKey` configured, the login is delayed and
   the user is redirected to :class:`~integreat_cms.cms.views.authentication.mfa.mfa_login_view.MfaLoginView`
3. A 2FA assertion challenge is requested via an AJAX call to :class:`~integreat_cms.cms.views.authentication.mfa.mfa_assert_view.MfaAssertView`
4. The browser sends the challenge to the 2FA key token and receives an assertion response
5. The key's assertion response is also sent via AJAX to :class:`~integreat_cms.cms.views.authentication.mfa.mfa_verify_view.MfaVerifyView`
6. If the validation was successfull, the user is logged in and redirected to the entry dashboard
7. If the validation was not successfull, an error message it displayed and the user can try again
"""
