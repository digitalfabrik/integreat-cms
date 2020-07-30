from django.contrib.auth.forms import SetPasswordForm
from django.utils.translation import ugettext as _


class PasswordResetConfirmForm(SetPasswordForm):
    """
    Form for resetting passwords
    """

    error_messages = {
        "password_mismatch": _("The passwords do not match."),
    }
