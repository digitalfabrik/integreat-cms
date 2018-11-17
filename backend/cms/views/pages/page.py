from django import forms as django_forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import ModelForm
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render
from cms.models.page import Page, PageTranslation
from .page_form import PageForm


@method_decorator(login_required, name='dispatch')
class PageView(TemplateView):
    template_name = 'pages/page.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, page_translation_id=None):
        if page_translation_id:
            p = PageTranslation.objects.filter(
                id=page_translation_id).select_related('page').first()
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
        return render(request, self.template_name, {
            'form': form, **self.base_context})

    def post(self, request, page_translation_id=None):
        # TODO: error handling
        form = PageForm(request.POST, user=request.user)
        if form.is_valid():
            if form.data['submit_publish']:
                # TODO: handle status

                if page_translation_id:
                    form.save(page_translation_id=page_translation_id)
                else:
                    form.save()

                messages.success(request, 'Seite wurde erfolgreich erstellt.')
            else:
                messages.success(request, 'Seite wurde erfolgreich gespeichert.')
            # TODO: imporve messages
        else:
            messages.error(request, 'Es sind Fehler aufgetreten.')

        return render(request, self.template_name, {
            'form': form, **self.base_context})
