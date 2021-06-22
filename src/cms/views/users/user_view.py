import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required, permission_required
from ...forms import UserForm, UserProfileForm
from ...models import UserProfile
from ...utils.welcome_mail_utils import send_welcome_mail

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
@method_decorator(permission_required("auth.view_user"), name="dispatch")
@method_decorator(permission_required("auth.change_user"), name="post")
class UserView(TemplateView):
    """
    View for the user form and user profile form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/admin/user.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "user_form"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.users.user_form.UserForm` and
        :class:`~cms.forms.users.user_profile_form.UserProfileForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        user = get_user_model().objects.filter(id=kwargs.get("user_id")).first()
        user_profile = UserProfile.objects.filter(user=user).first()

        user_form = UserForm(instance=user)
        user_profile_form = UserProfileForm(instance=user_profile)

        if user and not user.is_active:
            messages.info(request, _("Pending account activation"))

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "user_form": user_form,
                "user_profile_form": user_profile_form,
            },
        )

    # pylint: disable=unused-argument, too-many-branches
    def post(self, request, *args, **kwargs):
        """
        Submit :class:`~cms.forms.users.user_form.UserForm` and
        :class:`~cms.forms.users.user_profile_form.UserProfileForm` and save :class:`~django.contrib.auth.models.User`
        and :class:`~cms.models.users.user_profile.UserProfile` objects

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        user_instance = (
            get_user_model().objects.filter(id=kwargs.get("user_id")).first()
        )
        user_profile_instance = UserProfile.objects.filter(user=user_instance).first()

        user_form = UserForm(data=request.POST, instance=user_instance)
        user_profile_form = UserProfileForm(
            data=request.POST, instance=user_profile_instance
        )

        if not user_form.is_valid() or not user_profile_form.is_valid():
            # Add error messages
            user_form.add_error_messages(request)
            user_profile_form.add_error_messages(request)
        elif not (
            user_form.cleaned_data["is_superuser"]
            or user_form.cleaned_data["is_staff"]
            or user_profile_form.cleaned_data["regions"]
        ):
            # Add error message
            messages.error(
                request,
                _(
                    "A user has to be either staff/superuser or needs to be restricted to at least one region."
                ),
            )
        elif not (
            user_profile_form.cleaned_data.get("send_activation_link")
            or user_form.cleaned_data["password"]
            or user_instance
        ):
            # Add error message
            messages.error(
                request,
                _("Please choose either to send an activation link or set a password."),
            )
        elif not user_form.has_changed() and not user_profile_form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save forms
            user_profile_form.instance.user = user_form.save()
            user_profile_form.save()
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
                    "edit_user",
                    user_id=user_form.instance.id,
                )
            # Add the success message
            messages.success(
                request,
                _('User "{}" was successfully saved').format(
                    user_profile_form.instance.full_user_name
                ),
            )

        if not user_form.instance.is_active:
            messages.info(request, _("Pending account activation"))

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "user_form": user_form,
                "user_profile_form": user_profile_form,
            },
        )
