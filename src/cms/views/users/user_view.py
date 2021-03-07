from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...forms import UserForm, UserProfileForm
from ...models import UserProfile


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class UserView(PermissionRequiredMixin, TemplateView):
    """
    View for the user form and user profile form
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_admin_users"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/admin/user.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "users"}

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

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "user_form": user_form,
                "user_profile_form": user_profile_form,
            },
        )

    # pylint: disable=unused-argument
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

        user_form = UserForm(request.POST, instance=user_instance)
        user_profile_form = UserProfileForm(
            request.POST, instance=user_profile_instance
        )

        # TODO: error handling
        if user_form.is_valid() and user_profile_form.is_valid():

            # Check if user is either superuser/staff or has assigned at least one region
            if (
                user_form.cleaned_data["is_superuser"]
                or user_form.cleaned_data["is_staff"]
                or user_profile_form.cleaned_data["regions"]
            ):
                user = user_form.save()
                user_profile_form.save(user=user)

                if user_form.has_changed() or user_profile_form.has_changed():
                    if user_instance:
                        messages.success(request, _("User was successfully saved"))
                    else:
                        messages.success(request, _("User was successfully created"))
                        return redirect(
                            "edit_user",
                            **{
                                "user_id": user.id,
                            }
                        )
                else:
                    messages.info(request, _("No changes detected."))
            else:
                messages.error(
                    request,
                    _(
                        "A user has to be either staff/superuser or needs to be restricted to at least one region."
                    ),
                )
        else:
            # TODO: improve messages
            messages.error(request, _("Errors have occurred."))

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "user_form": user_form,
                "user_profile_form": user_profile_form,
            },
        )
