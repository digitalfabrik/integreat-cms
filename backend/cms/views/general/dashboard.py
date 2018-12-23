from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'general/dashboard.html'
    base_context = {'current_menu_item': 'dashboard'}

    def get(self, request, *args, **kwargs):
        val = 'To be defined'
        return render(request, self.template_name,
                      {'key': val, **self.base_context})
