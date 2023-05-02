"""
This package contains views related to registering and deleting multi-factor-authentication keys.

Registering a FIDO key works as follows:

1. User needs to re-authenticate via
   :class:`~integreat_cms.cms.views.settings.webauthn.authenticate_modify_mfa_view.AuthenticateModifyMfaView`
2. :class:`~integreat_cms.cms.views.settings.webauthn.register_user_fido_key_view.RegisterUserFidoKeyView` is requested via ``GET`` to render
   the form
3. When submitting the form, :class:`~integreat_cms.cms.views.settings.webauthn.get_mfa_challenge_view.GetMfaChallengeView` is requested
   via an AJAX call to receive a registration challenge
4. The challenge is verified via an AJAX call to
   :class:`~integreat_cms.cms.views.settings.webauthn.register_user_fido_key_view.RegisterUserFidoKeyView` via ``POST``
5. If the verification was successful and the key was successfully registered, the user is redirected to the
   :class:`~integreat_cms.cms.views.settings.user_settings_view.UserSettingsView`
6. If the validation was not successful, an error message it displayed and the user can try again

Deleting a FIDO key works as follows:

1. User needs to re-authenticate via
   :class:`~integreat_cms.cms.views.settings.webauthn.authenticate_modify_mfa_view.AuthenticateModifyMfaView`
2. :class:`~integreat_cms.cms.views.settings.webauthn.delete_user_fido_key_view.DeleteUserFidoKeyView` is requested via ``GET`` to render the
   confirmation form
3. :class:`~integreat_cms.cms.views.settings.webauthn.delete_user_fido_key_view.DeleteUserFidoKeyView` is requested via ``POST`` to submit
   the confirmation form and delete the key from the database

"""
