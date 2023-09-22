"""
This package contains views related to the multi-factor-authentication login with FIDO2.

The 2FA login process with FIDO2 is as follows:

1. User tries to login with the :class:`~integreat_cms.cms.views.authentication.login_view.LoginView`
2. If the user has at least one :class:`~integreat_cms.cms.models.users.user_fido_key.FidoKey` configured, the login is delayed and
   the user is redirected to :class:`~integreat_cms.cms.views.authentication.webauthn.webauthn_login_view.WebAuthnLoginView`
3. A 2FA assertion challenge is requested via an AJAX call to :class:`~integreat_cms.cms.views.authentication.webauthn.webauthn_assert_view.WebAuthnAssertView`
4. The browser sends the challenge to the FIDO key token and receives an assertion response
5. The key's assertion response is also sent via AJAX to :class:`~integreat_cms.cms.views.authentication.webauthn.webauthn_verify_view.WebAuthnVerifyView`
6. If the validation was successful, the user is logged in and redirected to the entry dashboard
7. If the validation was not successful, an error message it displayed and the user can try again
"""
