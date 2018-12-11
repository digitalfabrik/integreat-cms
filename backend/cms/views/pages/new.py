from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render


@method_decorator(login_required, name='dispatch')
class NewPageView(TemplateView):
    template_name = 'pages/new.html'
    base_context = {'current_menu_item': 'pages'}


    def get(self, request, *args, **kwargs):
        form = 'To be defined'
        return render(request, self.template_name, {'form': form, **self.base_context})

    def post(self, request):
        form = 'To be defined'
        return render(request, self.template_name, {'form': form, **self.base_context})
