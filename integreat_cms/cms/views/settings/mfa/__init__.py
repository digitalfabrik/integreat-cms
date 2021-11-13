"""
This package contains views related to registering and deleting multi-factor-authentication keys.

Registering a 2FA key works as follows:

1. User needs to re-authenticate via
   :class:`~integreat_cms.cms.views.settings.mfa.authenticate_modify_mfa_view.AuthenticateModifyMfaView`
2. :class:`~integreat_cms.cms.views.settings.mfa.register_user_mfa_key_view.RegisterUserMfaKeyView` is requested via ``GET`` to render
   the form
3. When submitting the form, :class:`~integreat_cms.cms.views.settings.mfa.get_mfa_challenge_view.GetMfaChallengeView` is requested
   via an AJAX call to receive a registration challenge
4. The challenge is verified via an AJAX call to
   :class:`~integreat_cms.cms.views.settings.mfa.register_user_mfa_key_view.RegisterUserMfaKeyView` via ``POST``
5. If the verification was successful and the key was successfully registered, the user is redirected to the
   :class:`~integreat_cms.cms.views.settings.user_settings_view.UserSettingsView`
6. If the validation was not successfull, an error message it displayed and the user can try again

Deleting a 2FA key works as follows:

1. User needs to re-authenticate via
   :class:`~integreat_cms.cms.views.settings.mfa.authenticate_modify_mfa_view.AuthenticateModifyMfaView`
2. :class:`~integreat_cms.cms.views.settings.mfa.delete_user_mfa_key_view.DeleteUserMfaKeyView` is requested via ``GET`` to render the
   confirmation form
3. :class:`~integreat_cms.cms.views.settings.mfa.delete_user_mfa_key_view.DeleteUserMfaKeyView` is requested via ``POST`` to submit
   the confirmation form and delete the key from the database

"""
