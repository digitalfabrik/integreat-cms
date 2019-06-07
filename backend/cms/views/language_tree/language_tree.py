from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...models import Site
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class LanguageTreeView(TemplateView):
    template_name = 'language_tree/tree.html'
    base_context = {'current_menu_item': 'language_tree'}

    def get(self, request, *args, **kwargs):
        language_tree = Site.get_current_site(request).language_tree_nodes.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'language_tree': language_tree
            }
        )
