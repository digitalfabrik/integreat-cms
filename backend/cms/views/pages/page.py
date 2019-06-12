"""

Returns:
    [type]: [description]
"""
import os
import uuid
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.views.static import serve

from .page_form import PageForm, PageTranslationForm
from ...models import Page, PageTranslation, Site, Language
from ...page_xliff_converter import PageXliffHelper, XLIFFS_DIR


logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class PageView(TemplateView):
    template_name = 'pages/page.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):
        site = Site.objects.get(slug=kwargs.get('site_slug'))

        language = Language.objects.get(code=kwargs.get('language_code'))

        # get page and translation objects if they exist
        page = Page.objects.filter(id=kwargs.get('page_id')).first()
        page_translation = PageTranslation.objects.filter(
            page=page,
            language=language,
        ).first()

        page_form = PageForm(
            instance=page,
            site=site,
            language=language,
        )
        page_translation_form = PageTranslationForm(
            instance=page_translation,
        )

        return render(request, self.template_name, {
            **self.base_context,
            'page_form': page_form,
            'page_translation_form': page_translation_form,
            'page': page,
            'language': language,
            'languages': site.languages,
        })

    def post(self, request, *args, **kwargs):

        site = Site.objects.get(slug=kwargs.get('site_slug'))
        language = Language.objects.get(code=kwargs.get('language_code'))

        page_instance = Page.objects.filter(id=kwargs.get('page_id')).first()
        page_translation_instance = PageTranslation.objects.filter(
            page=page_instance,
            language=language,
        ).first()

        page_form = PageForm(
            request.POST,
            instance=page_instance,
            site=site,
            language=language,
        )
        page_translation_form = PageTranslationForm(
            request.POST,
            instance=page_translation_instance,
        )

        # TODO: error handling
        if page_form.is_valid() and page_translation_form.is_valid():

            page = page_form.save()
            page_translation = page_translation_form.save(
                page=page,
                language=language,
                user=request.user,
            )

            if page_form.has_changed() or page_translation_form.has_changed():
                published = page_translation.public and 'public' in page_translation_form.changed_data
                if page_form.data.get('submit_archive'):
                    # archive button has been submitted
                    messages.success(request, _('Page was successfully archived.'))
                elif not page_instance:
                    if published:
                        messages.success(request, _('Page was successfully created and published.'))
                    else:
                        messages.success(request, _('Page was successfully created.'))
                elif not page_translation_instance:
                    if published:
                        messages.success(request, _('Translation was successfully created and published.'))
                    else:
                        messages.success(request, _('Translation was successfully created.'))
                else:
                    if published:
                        messages.success(request, _('Translation was successfully published.'))
                    else:
                        messages.success(request, _('Translation was successfully saved.'))
            else:
                messages.info(request, _('No changes detected.'))

            return redirect('edit_page', **{
                'page_id': page.id,
                'site_slug': site.slug,
                'language_code': language.code,
            })

        messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            **self.base_context,
            'page_form': page_form,
            'page_translation_form': page_translation_form,
            'page': page_instance,
            'language': language,
            'languages': site.languages,
        })


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


@login_required
def view_page(request, page_id, site_slug, language_code):
    template_name = 'pages/page_view.html'
    page = Page.objects.get(id=page_id)

    page_translation = page.get_translation(language_code)

    return render(request,
                  template_name,
                  {"page_translation": page_translation}
                  )


@login_required
def download_page_xliff(request, page_id, site_slug, language_code):
    page = Page.objects.get(id=page_id)
    page_xliff_helper = PageXliffHelper()
    page_xliff_zip_file = page_xliff_helper.export_page_xliffs_to_zip(page)
    if page_xliff_zip_file and page_xliff_zip_file.startswith(XLIFFS_DIR):
        response = serve(request, page_xliff_zip_file.split(XLIFFS_DIR)[1], document_root=XLIFFS_DIR)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(page_xliff_zip_file.split(os.sep)[-1])
        return response
    raise Http404


@login_required
def upload_page(request, site_slug, language_code):
    if request.method == 'POST' and 'xliff_file' in request.FILES:
        page_xliff_helper = PageXliffHelper()
        xliff_file = request.FILES['xliff_file']
        if xliff_file and  xliff_file.name.endswith(('.zip', '.xliff', '.xlf')):
            filename = xliff_file.name
            file_path = os.path.join(XLIFFS_DIR, 'upload', str(uuid.uuid4()), filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as upload_file:
                for chunk in xliff_file.chunks():
                    upload_file.write(chunk)
            if filename.endswith('.zip'):
                page_xliff_helper.import_xliffs_zip_file(file_path, request.user)
            else:
                page_xliff_helper.import_xliff_file(file_path, request.user)

            page_xliff_helper.delete_tmp_in_xliff_folder(file_path)

    return redirect('pages', **{
                'site_slug': site_slug,
                'language_code': language_code,
            })
