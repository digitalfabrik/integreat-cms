"""

Returns:
    [type]: [description]
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render
from ...models import Page, PageTranslation, Site
from .page_form import PageForm


@method_decorator(login_required, name='dispatch')
class PageView(TemplateView):
    template_name = 'pages/page.html'
    base_context = {'current_menu_item': 'pages'}
    page_translation_id = None

    def get(self, request, *args, **kwargs):
        if self.page_translation_id:
            p = PageTranslation.objects.filter(
                id=self.page_translation_id).select_related('page').first()
            form = PageForm(initial={
                'order': p.page.order,
                'parent': p.page.parent,
                'icon': p.page.icon,
                'title': p.title,
                'text': p.text,
                'status': p.status,
                'language': p.language,
            })
        else:
            form = PageForm()
        form.fields['parent'].queryset = Page.objects.filter(
            site__slug=Site.get_current_site(request).slug
        )
        return render(request, self.template_name, {
            'form': form, **self.base_context})

    def post(self, request, site_slug):
        # TODO: error handling
        form = PageForm(request.POST, user=request.user)
        if form.is_valid():
            if self.page_translation_id:
                form.save_page(
                    site_slug=site_slug,
                    page_translation_id=self.page_translation_id,
                )
                messages.success(request, _('Page was saved successfully.'))
            else:
                form.save_page(
                    site_slug=site_slug,
                )
                messages.success(request, _('Page was created successfully.'))
            # TODO: improve messages
        else:
            messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            'form': form, **self.base_context})
