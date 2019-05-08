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
        site = Site.objects.get(slug=kwargs.get('site_slug'))
        page = Page.objects.filter(pk=kwargs.get('page_id', None)).first()
        language = Language.objects.get(code=kwargs.get('language_code'))
        languages = site.languages
        # limit possible parents to pages of current region
        parent_queryset = Page.objects.filter(
            site__slug=site.slug
        )
        initial = {}
        public = False

        if page:
            initial['parent'] = page.parent
            # remove children from possible parents
            children = page.get_descendants(include_self=True)
            parent_queryset = parent_queryset.difference(children)
            page_translation = page.get_translation(language.code)
            if page_translation:
                initial.update({
                    'title': page_translation.title,
                    'text': page_translation.text,
                    'status': page_translation.status,
                    'public': page_translation.public,
                })
                public = page_translation.public
        form = PageForm(initial=initial)
        form.fields['parent'].queryset = parent_queryset

        return render(request, self.template_name, {
            'form': form,
            'public': public,
            'page': page,
            'language': language,
            'languages': languages,
            **self.base_context,
        })

    def post(self, request, *args, **kwargs):
        site_slug = kwargs.get('site_slug')
        page_id = kwargs.get('page_id', None)
        language_code = kwargs.get('language_code')
        # TODO: error handling
        form = PageForm(request.POST, user=request.user)
        if form.is_valid():
            if form.data.get('submit_publish'):
                page = form.save_page(
                    site_slug=site_slug,
                    language_code=language_code,
                    page_id=page_id,
                    publish=True
                )
                if page_id:
                    messages.success(request, _('Page was successfully published.'))
                else:
                    page_id = page.id
                    messages.success(request, _('Page was successfully created and published.'))
            elif form.data.get('submit_archive'):
                page = form.save_page(
                        site_slug=site_slug,
                        language_code=language_code,
                        page_id=page_id,
                        archived=True
                    )
                if page_id:
                    messages.success(request, _('Page was successfully saved.'))
                else:
                    page_id = page.id
                    messages.success(request, _('Page was successfully created.'))
            else:
                page = form.save_page(
                    site_slug=site_slug,
                    language_code=language_code,
                    page_id=page_id,
                    publish=False
                )
                if page_id:
                    messages.success(request, _('Page was successfully saved.'))
                else:
                    page_id = page.id
                    messages.success(request, _('Page was successfully created.'))
        else:
            messages.error(request, _('Errors have occurred.'))
        if page_id:
            return redirect('edit_page', **{
                'page_id': page_id,
                'site_slug': site_slug,
                'language_code': language_code,
            })
        return redirect('new_page', **kwargs)


@login_required
def archive_page(request, page_id, site_slug, language_code):
    page = Page.objects.get(id=page_id)
    page.public = False
    page.archived = True
    page.save()

    messages.success(request, _('Page was successfully archived.'))

    return redirect('pages', **{
                'site_slug': site_slug,
                'language_code': language_code,
            })


@login_required
def restore_page(request, page_id, site_slug, language_code):
    page = Page.objects.get(id=page_id)
    page.archived = False
    page.save()

    messages.success(request, _('Page was successfully restored.'))

    return redirect('pages', **{
                'site_slug': site_slug,
                'language_code': language_code,
            })