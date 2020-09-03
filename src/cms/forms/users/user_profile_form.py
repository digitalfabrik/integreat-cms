"""
Form for creating a user object
"""
import logging

from django import forms

from ...models import UserProfile


logger = logging.getLogger(__name__)


class UserProfileForm(forms.ModelForm):
    """
    Form for creating and modifying user profile objects
    """

    class Meta:
        model = UserProfile
        fields = ["regions", "organization"]

    def __init__(self, data=None, instance=None):

        logger.info(
            "UserProfileForm instantiated with data %s and instance %s", data, instance
        )

        # Instantiate ModelForm
        super().__init__(data=data, instance=instance)

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):

        logger.info(
            "UserProfileForm saved with cleaned data %s and changed data %s",
            self.cleaned_data,
            self.changed_data,
        )

        logger.info("UserProfileForm saved with args %s and kwargs %s", args, kwargs)

        # pop kwarg to make sure the super class does not get this param
        user = kwargs.pop("user", None)

        if not self.instance.id:
            # don't commit saving of ModelForm, because required user field is still missing
            kwargs["commit"] = False

        # save ModelForm
        user_profile = super().save(*args, **kwargs)

        if not self.instance.id:
            user_profile.user = user
            user_profile.save()
            # check if called from UserProfileForm or RegionUserProfileForm
            if "regions" in self.cleaned_data:
                # regions can't be saved if commit=False on the ModelForm, so we have to save them explicitly
                user_profile.regions.set(self.cleaned_data["regions"])

        return user_profile
