"""

Returns:
    [type]: [description]
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from ...models import Page, Site, Language
from .page_form import PageForm


@method_decorator(login_required, name='dispatch')
class PageView(TemplateView):
    template_name = 'pages/page.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):
        site_slug = kwargs.get('site_slug')
        page_id = kwargs.get('page_id', None)
        # limit possible parents to pages of current region
        parent_queryset = Page.objects.filter(
            site__slug=site_slug
        )
        if page_id:
            # TODO: get current language
            page = Page.objects.get(pk=page_id)
            # remove children from possible parents
            children = page.get_descendants(include_self=True)
            parent_queryset = parent_queryset.difference(children)
            page_translation = page.get_translation('de')
            form = PageForm(initial={
                'title': page_translation.title,
                'text': page_translation.text,
                'status': page_translation.status,
                'language': page_translation.language,
                'public': page_translation.public,
                'parent': page.parent
            })
            public = page_translation.public
        else:
            form = PageForm()
            public = False
        form.fields['parent'].queryset = parent_queryset
        form.fields['language'].queryset = Language.objects.filter(
            language_tree_nodes__in=Site.objects.get(slug=site_slug).language_tree_nodes.all()
        )
        return render(request, self.template_name, {
            'form': form, 'public': public, **self.base_context})

    def post(self, request, *args, **kwargs):
        site_slug = kwargs.get('site_slug')
        page_id = kwargs.get('page_id', None)
        # TODO: error handling
        form = PageForm(request.POST, user=request.user)
        if form.is_valid():
            if form.data.get('submit_publish'):
                page = form.save_page(
                    site_slug=site_slug,
                    page_id=page_id,
                    publish=True
                )
                if page_id:
                    messages.success(request, _('Page was published successfully.'))
                else:
                    messages.success(request, _('Page was created and published successfully.'))
            else:
                page = form.save_page(
                    site_slug=site_slug,
                    page_id=page_id,
                    publish=False
                )
                if page_id:
                    messages.success(request, _('Page was saved successfully.'))
                else:
                    messages.success(request, _('Page was created successfully.'))
            return redirect(page)
        messages.error(request, _('Errors have occurred.'))
        if page_id:
            page = Page.objects.get(pk=page_id)
            return redirect(page)
        return redirect('new_page', kwargs={'site_slug': site_slug})
