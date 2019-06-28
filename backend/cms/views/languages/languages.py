from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render

from .language_form import LanguageForm
from ...models import Language
from ...decorators import staff_required


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class LanguageListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_languages'
    raise_exception = True

    template_name = 'languages/list.html'
    base_context = {'current_menu_item': 'languages'}

    def get(self, request, *args, **kwargs):
        languages = Language.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'languages': languages
            }
        )


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class LanguageView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_languages'
    raise_exception = True

    template_name = 'languages/language.html'
    base_context = {'current_menu_item': 'languages'}
    language_code = None

    def get(self, request, *args, **kwargs):
        self.language_code = self.kwargs.get('language_code', None)
        if self.language_code:
            language = Language.objects.get(code=self.language_code)
            form = LanguageForm(initial={
                'name': language.name,
                'code': language.code,
                'text_direction': language.text_direction,
            })
        else:
            form = LanguageForm()
        return render(request, self.template_name, {
            'form': form, **self.base_context})

    def post(self, request, language_code=None):
        # TODO: error handling
        form = LanguageForm(request.POST)
        if form.is_valid():
            if language_code:
                form.save_language(language_code=language_code)
                messages.success(request, _('Language saved successfully.'))
            else:
                form.save_language()
                messages.success(request, _('Language created successfully'))
            # TODO: improve messages
        else:
            messages.error(request, _('An error has occurred.'))

        return render(request, self.template_name, {
            'form': form, **self.base_context})
