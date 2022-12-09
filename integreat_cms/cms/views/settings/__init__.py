"""
This package contains all views related to settings
"""
from .user_settings_view import UserSettingsView
from .dismiss_tutorial_view import DismissTutorial

from .mfa.authenticate_modify_mfa_view import AuthenticateModifyMfaView
from .mfa.delete_user_mfa_key_view import DeleteUserMfaKeyView
from .mfa.get_mfa_challenge_view import GetMfaChallengeView
from .mfa.register_user_mfa_key_view import RegisterUserMfaKeyView
from .totp_register_view import TOTPRegisterView
from .totp_delete_view import TOTPDeleteView
