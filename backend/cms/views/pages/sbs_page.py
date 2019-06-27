"""
    Side by side view
"""

from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from .page_form import PageTranslationForm
from ...models import Page, Site, Language
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class SBSPageView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.view_pages'
    raise_exception = True

    template_name = 'pages/sbs_page.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):

        site = Site.objects.get(slug=kwargs.get('site_slug'))
        page = Page.objects.get(pk=kwargs.get('page_id'))

        source_language_code, target_language_code = kwargs.get('language_code').split('__')
        source_language = Language.objects.get(code=source_language_code)
        target_language = Language.objects.get(code=target_language_code)

        source_page_translation = page.get_translation(source_language.code)
        target_page_translation = page.get_translation(target_language.code)

        if not source_page_translation:
            return redirect('edit_page', **{
                'page_id': page.id,
                'site_slug': site.slug,
                'language_code': source_language.code,
            })

        page_translation_form = PageTranslationForm(
            instance=target_page_translation,
        )

        return render(request, self.template_name, {
            **self.base_context,
            'page_translation_form': page_translation_form,
            'source_page_translation': source_page_translation,
            'source_language': source_language,
            'target_language': target_language,
        })

    def post(self, request, *args, **kwargs):

        if not request.user.has_perm('cms.edit_pages'):
            raise PermissionDenied

        site = Site.objects.get(slug=kwargs.get('site_slug'))
        page = Page.objects.get(pk=kwargs.get('page_id'))

        source_language_code, target_language_code = kwargs.get('language_code').split('__')
        source_language = Language.objects.get(code=source_language_code)
        target_language = Language.objects.get(code=target_language_code)

        source_page_translation = page.get_translation(source_language.code)
        page_translation_instance = page.get_translation(language_code=target_language_code)

        if not source_page_translation:
            return redirect('edit_page', **{
                'page_id': page.id,
                'site_slug': site.slug,
                'language_code': source_language.code,
            })

        if not page_translation_instance:
            # copy object instance because required status field is missing otherwise
            page_translation_instance = source_page_translation
            page_translation_instance.id = None
            page_translation_instance.language = target_language
            page_translation_instance.creator = request.user
            page_translation_instance.public = False
            page_translation_instance.save()
            created = True
        else:
            created = False

        page_translation_form = PageTranslationForm(
            request.POST,
            instance=page_translation_instance,
        )
        page_translation_form.fields['status'].required = False

        if page_translation_form.is_valid():
            page_translation_form.save()
            if page_translation_form.has_changed():
                if created:
                    messages.success(request, _('Translation was successfully created.'))
                else:
                    messages.success(request, _('Translation was successfully saved.'))
            else:
                messages.info(request, _('No changes detected.'))
        else:
            messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            **self.base_context,
            'page_translation_form': page_translation_form,
            'source_page_translation': source_page_translation,
            'source_language': source_language,
            'target_language': target_language,
        })
