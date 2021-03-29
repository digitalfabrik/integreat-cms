from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...forms import RegionUserForm, RegionUserProfileForm
from ...models import Region
from ...utils.account_activation_utils import send_activation_link


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class RegionUserView(PermissionRequiredMixin, TemplateView):
    """
    View for the user form and user profile form of region users
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_region_users"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/region/user.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "region_users_form"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.users.user_form.UserForm` and :class:`~cms.forms.users.user_profile_form.UserProfileForm` for region users

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)

        # filter region users to make sure no users from other regions can be changed through this view
        user = region.users.filter(id=kwargs.get("user_id")).first()
        user_profile = user.profile if user else None

        region_user_form = RegionUserForm(instance=user)
        user_profile_form = RegionUserProfileForm(instance=user_profile)

        if user and not user.is_active:
            messages.info(request, _("Pending account activation"))

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "user_form": region_user_form,
                "user_profile_form": user_profile_form,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """
        Submit :class:`~cms.forms.users.user_form.UserForm` and
        :class:`~cms.forms.users.user_profile_form.UserProfileForm` and save :class:`~django.contrib.auth.models.User`
        and :class:`~cms.models.users.user_profile.UserProfile` objects for region users

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)

        # filter region users to make sure no users from other regions can be changed through this view
        user_instance = region.users.filter(id=kwargs.get("user_id")).first()
        user_profile_instance = user_instance.profile if user_instance else None

        region_user_form = RegionUserForm(request.POST, instance=user_instance)
        user_profile_form = RegionUserProfileForm(
            request.POST, instance=user_profile_instance
        )

        # TODO: error handling
        if region_user_form.is_valid() and user_profile_form.is_valid():

            # check if either activation link is set or password is set or user already exists
            if (
                user_profile_form.cleaned_data["send_activation_link"]
                or region_user_form.cleaned_data["password"]
                or user_instance
            ):

                user = region_user_form.save()
                user_profile_form.save(user=user, region=region)

                if user_profile_form.cleaned_data["send_activation_link"]:
                    send_activation_link(request, user)

                if region_user_form.has_changed() or user_profile_form.has_changed():
                    if user_instance:
                        messages.success(request, _("User was successfully saved"))
                    else:
                        messages.success(request, _("User was successfully created"))
                        return redirect(
                            "edit_region_user",
                            **{
                                "region_slug": region.slug,
                                "user_id": user.id,
                            }
                        )
                else:
                    messages.info(request, _("No changes detected."))
            else:
                messages.error(
                    request,
                    _(
                        "Please choose either to send an activation link or set a password."
                    ),
                )
        else:
            # TODO: improve messages for region users
            messages.error(request, _("Errors have occurred."))

        if not region_user_form.cleaned_data["is_active"]:
            messages.info(request, _("Pending account activation"))

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "user_form": region_user_form,
                "user_profile_form": user_profile_form,
            },
        )
