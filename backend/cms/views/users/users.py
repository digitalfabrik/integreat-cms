from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from .user_form import UserForm, UserProfileForm
from ...models.user_profile import UserProfile
from ...decorators import staff_required


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class UserListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.change_user'
    raise_exception = True

    template_name = 'users/admin/list.html'
    base_context = {'current_menu_item': 'users'}

    def get(self, request, *args, **kwargs):
        users = get_user_model().objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'users': users
            }
        )


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class UserView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.change_user'
    raise_exception = True

    template_name = 'users/admin/user.html'
    base_context = {'current_menu_item': 'users'}

    def get(self, request, *args, **kwargs):

        user = get_user_model().objects.filter(id=kwargs.get('user_id')).first()
        user_profile = UserProfile.objects.filter(user=user).first()

        user_form = UserForm(instance=user)
        user_profile_form = UserProfileForm(instance=user_profile)

        return render(request, self.template_name, {
            **self.base_context,
            'user_form': user_form,
            'user_profile_form': user_profile_form,
        })

    def post(self, request, *args, **kwargs):

        user_instance = get_user_model().objects.filter(id=kwargs.get('user_id')).first()
        user_profile_instance = UserProfile.objects.filter(user=user_instance).first()

        user_form = UserForm(
            request.POST,
            instance=user_instance
        )
        user_profile_form = UserProfileForm(
            request.POST,
            instance=user_profile_instance
        )

        # TODO: error handling
        if user_form.is_valid() and user_profile_form.is_valid():

            user = user_form.save()
            user_profile_form.save(user=user)

            if user_form.has_changed() or user_profile_form.has_changed():
                if user_instance:
                    messages.success(request, _('User was successfully saved.'))
                else:
                    messages.success(request, _('User was successfully created.'))
                    return redirect('edit_user', **{
                        'user_id': user.id,
                    })
            else:
                messages.info(request, _('No changes detected.'))
        else:
            # TODO: improve messages
            messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            **self.base_context,
            'user_form': user_form,
            'user_profile_form': user_profile_form,
        })


@staff_required
@login_required
def delete_user(request, user_id):

    get_user_model().objects.get(id=user_id).delete()

    messages.success(request, _('User was successfully deleted.'))

    return redirect('users')
