import logging

from django.contrib.auth.forms import SetPasswordForm

logger = logging.getLogger(__name__)


class ActivationForm(SetPasswordForm):
    """
    Form for setting password and activating account
    """

    def save(self, commit=False):
        """Overrides save method to additionally activate inactive accounts

        :return: the user instance that was saved
        :rtype: ~django.contrib.auth.models.User
        """
        super().save(commit)
        self.user.is_active = True
        self.user.save()
        logger.info("Account activation for user %r was successful", self.user.profile)
        return self.user
