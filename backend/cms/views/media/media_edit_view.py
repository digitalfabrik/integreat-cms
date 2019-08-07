from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ..utils.file_utils import save_file
from ...models import DocumentForm, Document
from ...models.region import Region
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class MediaEditView(TemplateView):
    template_name = 'media/mediaedit.html'
    base_context = {'current_menu_item': 'media'}

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('region_slug')
        region = Region.objects.get(slug=slug)
        document_id = kwargs.get('document_id')
        form = DocumentForm()
        if document_id != '0':
            document = Document.objects.get(pk=document_id)
            form = DocumentForm(instance=document)

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'form': form,
                'region_slug': region.slug,
            }
        )

    def post(self, request, *args, **kwargs):
        # current region
        region = Region.objects.get(slug=kwargs.get('region_slug'))

        result = save_file(request)

        if result.get('status') == 1:
            return redirect('media', **{'region_slug': region.slug})
        return render(request, self.template_name, {'form': result.get('form')})
