"""
This package contains all views related to multi-factor authentication
"""
from .mfa import (
    register_mfa_key,
    GetChallengeView,
    AuthenticateModifyMfaView,
    AddMfaKeyView,
    DeleteMfaKey,
)
