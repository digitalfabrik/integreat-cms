"""
Form for creating a user object
"""

import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as Role
from django.contrib.auth.password_validation import validate_password, password_validators_help_texts
from django.utils.translation import ugettext_lazy as _

from ...models.user_profile import UserProfile


logger = logging.getLogger(__name__)


class UserForm(forms.ModelForm):

    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        required=False
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password],
        help_text=password_validators_help_texts
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email',
                  'is_staff', 'is_active', 'is_superuser']

    def __init__(self, *args, **kwargs):

        logger.info('New UserForm instantiated with args {} and kwargs {}'.format(args, kwargs))

        # instantiate ModelForm
        super(UserForm, self).__init__(*args, **kwargs)

        # check if user instance already exists
        if self.instance.id:
            # set initial role data
            self.fields['roles'].initial = self.instance.groups.all()
            # don't require password if user already exists
            self.fields['password'].required = False

    def save(self, *args, **kwargs):

        logger.info('UserForm saved with args {} and kwargs {}'.format(args, kwargs))

        # save ModelForm
        user = super(UserForm, self).save(*args, **kwargs)

        # check if password field was changed
        if self.cleaned_data['password']:
            # change password
            user.set_password(self.cleaned_data['password'])
            user.save()

        # assign all selected roles which the user does not have already
        for role in set(self.cleaned_data['roles']) - set(user.groups.all()):
            role.user_set.add(user)
            logger.info('The role {} was assigned to the user {}'.format(role, user))

        # remove all unselected roles which the user had before
        for role in set(user.groups.all()) - set(self.cleaned_data['roles']):
            role.user_set.remove(user)
            logger.info('The role {} was removed from the user {}'.format(role, user))

        return user


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ['regions', 'organization']

    def save(self, *args, **kwargs):

        logger.info('UserProfileForm saved with args {} and kwargs {}'.format(args, kwargs))

        # pop kwarg to make sure the super class does not get this param
        user = kwargs.pop('user', None)

        if not self.instance.id:
            # don't commit saving of ModelForm, because required user field is still missing
            kwargs['commit'] = False

        # save ModelForm
        user_profile = super(UserProfileForm, self).save(*args, **kwargs)

        if not self.instance.id:
            user_profile.user = user
            user_profile.save()
            # check if called from UserProfileForm or RegionUserProfileForm
            if 'regions' in self.cleaned_data:
                # regions can't be saved if commit=False on the ModelForm, so we have to save them explicitly
                user_profile.regions = self.cleaned_data['regions']
                user_profile.save()

        return user_profile
