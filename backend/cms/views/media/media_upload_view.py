from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from ...models import DocumentForm
from ...models.site import Site
from ..utils import save_file


@method_decorator(login_required, name='dispatch')
class MediaUploadView(TemplateView):
    template_name = 'media/mediaupload.html'
    base_context = {'current_menu_item': 'media'}

    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'form': DocumentForm(),
            }
        )

    def post(self, request, *args, **kwargs):
        # current site
        site = Site.objects.get(slug=kwargs.get('site_slug'))

        result = save_file(request)

        if result.get('status') == 1:
            return redirect('media', **{'site_slug': site.slug})
        else:
            return render(request, self.template_name, {'form': result.get('form')})
