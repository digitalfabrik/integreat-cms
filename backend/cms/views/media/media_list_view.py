from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ...models.region import Region
from ...models import Document
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class MediaListView(TemplateView):
    template_name = 'media/medialist.html'
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


@login_required
@region_permission_required
def delete_file(request, document_id, region_slug):
    region = Region.objects.get(slug=region_slug)

    if request.method == 'POST':
        document = Document.objects.get(pk=document_id)
        document.delete()

    return redirect('media', **{'region_slug': region.slug})
