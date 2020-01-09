from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@method_decorator(login_required, name='dispatch')
class UserSettingsView(TemplateView):
    template_name = 'settings/user.html'

    @never_cache
    def get(self, request, *args, **kwargs):
        user = request.user

        return render(request,
                      self.template_name,
                      {'keys': user.mfa_keys.all()})
