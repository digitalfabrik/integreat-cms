"""
This package contains all views related to settings
"""

from __future__ import annotations

from .dismiss_tutorial_view import DismissTutorial
from .totp_delete_view import TOTPDeleteView
from .totp_register_view import TOTPRegisterView
from .user_settings_view import UserSettingsView
from .webauthn.authenticate_modify_mfa_view import AuthenticateModifyMfaView
from .webauthn.delete_user_fido_key_view import DeleteUserFidoKeyView
from .webauthn.get_mfa_challenge_view import GetMfaChallengeView
from .webauthn.register_user_fido_key_view import RegisterUserFidoKeyView
