"""
Forms related to the user creation and more
"""
from django.contrib.auth.forms import SetPasswordForm
from django.utils.translation import ugettext as _


class PasswordResetConfirmForm(SetPasswordForm):
    """
    Form for resetting Passwords
    """
    error_messages = {
        'password_mismatch': _("The passwords do not match."),
    }
