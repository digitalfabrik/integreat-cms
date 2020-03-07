from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache

from ...forms.users import UserEmailForm, UserPasswordForm


@method_decorator(login_required, name='dispatch')
class UserSettingsView(TemplateView):
    template_name = 'settings/user.html'

    @never_cache
    def get(self, request, *args, **kwargs):

        user = request.user
        user_email_form = UserEmailForm(instance=user)
        user_password_form = UserPasswordForm(instance=user)

        return render(
            request,
            self.template_name,
            {
                'keys': user.mfa_keys.all(),
                'user_email_form': user_email_form,
                'user_password_form': user_password_form,
            }
        )

    # pylint: disable=unused-argument, too-many-branches
    def post(self, request, *args, **kwargs):

        user = request.user

        if request.POST.get('submit_form') == 'email_form':
            user_email_form = UserEmailForm(
                request.POST,
                instance=user
            )
            if not user_email_form.is_valid():

                # Add error messages
                for field in user_email_form:
                    for error in field.errors:
                        messages.error(request, _(error))
                for error in user_email_form.non_field_errors():
                    messages.error(request, _(error))

            elif not user_email_form.has_changed():
                messages.info(request, _('No changes detected.'))
            else:
                user_email_form.save()
                messages.success(request, _('E-mail-address was successfully saved.'))

        elif request.POST.get('submit_form') == 'password_form':
            user_password_form = UserPasswordForm(
                request.POST,
                instance=user
            )
            if not user_password_form.is_valid():

                # Add error messages
                for field in user_password_form:
                    for error in field.errors:
                        messages.error(request, _(error))
                for error in user_password_form.non_field_errors():
                    messages.error(request, _(error))

            elif not user_password_form.has_changed():
                messages.info(request, _('No changes detected.'))
            else:
                user = user_password_form.save()
                # Prevent user from being logged out after password has changed
                update_session_auth_hash(request, user)
                messages.success(request, _('Password was successfully saved.'))

        return redirect('user_settings')
