from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from ...models.site import Site
from ...models import Document


@method_decorator(login_required, name='dispatch')
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
def delete_file(request, document_id, site_slug):
    site = Site.objects.get(slug=site_slug)

    if request.method == 'POST':
        document = Document.objects.get(pk=document_id)
        document.delete()

    return redirect('media', **{'site_slug': site.slug})
