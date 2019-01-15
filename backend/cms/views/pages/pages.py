from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render
from cms.models.page import Page


@method_decorator(login_required, name='dispatch')
class PageTreeView(TemplateView):
    template_name = 'pages/tree.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):
        pages = Page.get_tree_view()

        return render(request,
                      self.template_name,
                      {**self.base_context,
                       'pages': pages})
