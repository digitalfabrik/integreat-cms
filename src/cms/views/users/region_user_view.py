import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required, permission_required
from ...forms import RegionUserForm, RegionUserProfileForm
from ...models import Region
from ...utils.welcome_mail_utils import send_welcome_mail

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("auth.view_user"), name="dispatch")
@method_decorator(permission_required("auth.change_user"), name="post")
class RegionUserView(TemplateView):
    """
    View for the user form and user profile form of region users
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/region/user.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "region_user_form"}

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

        region_user_form = RegionUserForm(data=request.POST, instance=user_instance)
        user_profile_form = RegionUserProfileForm(
            data=request.POST, instance=user_profile_instance
        )
        user_profile_form.instance.region = region

        if not region_user_form.is_valid() or not user_profile_form.is_valid():
            # Add error messages
            region_user_form.add_error_messages(request)
            user_profile_form.add_error_messages(request)
        elif not (
            user_profile_form.cleaned_data["send_activation_link"]
            or region_user_form.cleaned_data["password"]
            or user_instance
        ):
            # Add error message
            messages.error(
                request,
                _("Please choose either to send an activation link or set a password."),
            )
        elif not region_user_form.has_changed() or not user_profile_form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save forms
            user_profile_form.instance.user = region_user_form.save()
            user_profile_form.save()
            user_profile_form.instance.regions.add(region)
            # Check if user was created
            if not user_instance:
                # Send activation link or welcome mail
                activation = user_profile_form.cleaned_data.get("send_activation_link")
                send_welcome_mail(request, user_form.instance, activation)
                # Add the success message and redirect to the edit page
                messages.success(
                    request,
                    _('User "{}" was successfully created').format(
                        user_profile_form.instance.full_user_name
                    ),
                )
                return redirect(
                    "edit_region_user",
                    region_slug=region.slug,
                    user_id=region_user_form.instance.id,
                )
            # Add the success message
            messages.success(
                request,
                _('User "{}" was successfully saved').format(
                    user_profile_form.instance.full_user_name
                ),
            )

        if not region_user_form.instance.is_active:
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
