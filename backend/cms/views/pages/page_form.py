from django import forms
from cms.models.page import Page, PageTranslation


class PageForm(forms.ModelForm):
    order = forms.IntegerField(required=False)
    parent = forms.ModelChoiceField(queryset=Page.objects.all(),
                                    required=False)
    icon = forms.ImageField(required=False)

    class Meta:
        model = PageTranslation
        fields = ['title', 'text', 'status', 'language']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(PageForm, self).__init__(*args, **kwargs)
        # TODO: get available languages from site settings
        self.fields['language'] = forms.ChoiceField(
            choices=[('de', 'Deutsch'),
                     ('ar', 'Arabisch'),
                     ('fa', 'Farsi'),
                     ('fr', 'Französisch'),
                     ('tr', 'Türkisch')])

    def save_page(self, page_translation_id=None):
        # TODO: version, active_version
        if page_translation_id:
            p = PageTranslation.objects.filter(
                id=page_translation_id).select_related('page').first()

            # save page
            page = Page.objects.get(id=p.page.id)
            page.order = self.cleaned_data['order']
            page.parent = self.cleaned_data['parent']
            page.icon = self.cleaned_data['icon']
            page.save()

            # save page translation
            page_translation = PageTranslation.objects.get(id=p.id)
            page_translation.title = self.cleaned_data['title']
            page_translation.text = self.cleaned_data['text']
            page_translation.status = self.cleaned_data['status']
            page_translation.language = self.cleaned_data['language']
            page_translation.save()
        else:
            # create page
            page = Page.objects.create(
                order=self.cleaned_data['order'],
                parent=self.cleaned_data['parent'],
                icon=self.cleaned_data['icon'])

            # create page translation
            page_translation = PageTranslation.objects.create(
                title=self.cleaned_data['title'],
                text=self.cleaned_data['text'],
                status=self.cleaned_data['status'],
                language=self.cleaned_data['language'],
                page=page,
                user=self.user
            )

    def clean_order(self):
        order = self.cleaned_data['order'] if self.cleaned_data['order'] else 0
        return order
