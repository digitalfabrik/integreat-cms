from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import staff_required, region_permission_required

@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class SettingsView(TemplateView):
    template_name = 'settings/settings.html'
    base_context = {'current_menu_item': 'region_settings'}

    def get(self, request, *args, **kwargs):
        settings = 'to be defined'

        return render(request,
                      self.template_name,
                      {**self.base_context,
                       'settings': settings})

@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class AdminSettingsView(TemplateView):
    template_name = 'settings/admin_settings.html'
    base_context = {'current_menu_item': 'admin_settings'}

    def get(self, request, *args, **kwargs):
        settings = 'to be defined'

        return render(request,
                      self.template_name,
                      {**self.base_context,
                       'settings': settings})
