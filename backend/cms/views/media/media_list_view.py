from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Document


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class MediaListView(TemplateView):
    template_name = 'media/list.html'
    base_context = {'current_menu_item': 'media'}

    def get(self, request, *args, **kwargs):
        documents = Document.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'documents': documents
            }
        )
