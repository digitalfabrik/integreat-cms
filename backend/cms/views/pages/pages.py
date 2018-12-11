from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render


@method_decorator(login_required, name='dispatch')
class PagesView(TemplateView):
    template_name = 'pages/tree.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {**self.base_context})
