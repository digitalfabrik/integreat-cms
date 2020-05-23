"""
Form for creating a region user object
"""
import logging

from django.contrib.auth import get_user_model

from .user_form import UserForm


logger = logging.getLogger(__name__)


class RegionUserForm(UserForm):

    class Meta:
        model = get_user_model()
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active'
        ]

    def __init__(self, data=None, instance=None):

        logger.info('RegionUserForm instantiated with data %s and instance %s', data, instance)

        # Instantiate ModelForm
        super(RegionUserForm, self).__init__(data=data, instance=instance)

    def save(self, *args, **kwargs):

        logger.info('RegionUserForm saved with cleaned data %s and changed data %s', self.cleaned_data, self.changed_data)

        # save ModelForm
        return super(RegionUserForm, self).save(*args, **kwargs)
