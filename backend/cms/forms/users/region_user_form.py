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
