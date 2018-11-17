from django.contrib.auth.forms import SetPasswordForm


class PasswordResetConfirmForm(SetPasswordForm):
    error_messages = {
        'password_mismatch': "Die Passwörter stimmen nicht überein.",
    }
