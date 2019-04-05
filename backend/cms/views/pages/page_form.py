"""
Form for creating a page object
"""

from django import forms
from ...models.page import Page, PageTranslation, Site


class PageForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    order = forms.IntegerField(required=False)
    parent = forms.ModelChoiceField(queryset=Page.objects.all(), required=False)
    icon = forms.ImageField(required=False)

    class Meta:
        model = PageTranslation
        fields = ['title', 'text', 'status', 'language']


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(PageForm, self).__init__(*args, **kwargs)

    def save_page(self, site_slug, page_translation_id=None):
        """Function to create or update a page
            page_translation_id ([Integer], optional): Defaults to None. If it's not set creates
            a page or update the page with the given page id.
        """

        # TODO: version, active_version
        if page_translation_id:
            page_object = PageTranslation.objects.filter(
                id=page_translation_id).select_related('page').first()

            # save page
            page = Page.objects.get(id=page_object.page.id)
            page.order = self.cleaned_data['order']
            page.parent = self.cleaned_data['parent']
            page.icon = self.cleaned_data['icon']
            page.save()

            # save page translation
            page_translation = PageTranslation.objects.get(id=page_object.id)
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
                icon=self.cleaned_data['icon'],
                site=Site.objects.get(slug=site_slug),
            )

            # create page translation
            page_translation = PageTranslation.objects.create(
                title=self.cleaned_data['title'],
                text=self.cleaned_data['text'],
                status=self.cleaned_data['status'],
                language=self.cleaned_data['language'],
                page=page,
                creator=self.user
            )

    def clean_order(self):
        """Function to clean the order of the form
        Returns:
            order: Ordered list
        """
        order = self.cleaned_data['order'] if self.cleaned_data['order'] else 0
        return order
