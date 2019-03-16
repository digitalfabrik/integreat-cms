"""
Forms related to the user creation and more
"""
from django.contrib.auth.forms import SetPasswordForm


class PasswordResetConfirmForm(SetPasswordForm):
    """
    Form for resetting Passwords
    """
    error_messages = {
        'password_mismatch': "Die Passwörter stimmen nicht überein.",
    }
