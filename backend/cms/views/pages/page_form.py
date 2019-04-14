"""
Form for creating a page object and page translation object
"""

from django import forms
from django.utils.text import slugify
from ...models import Page, PageTranslation, Site
from ..general import POSITION_CHOICES


class PageForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    position = forms.ChoiceField(choices=POSITION_CHOICES)
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

        slug = slugify(self.cleaned_data['title'])
        # make sure the slug derived from the title is unique
        if (
                (
                    # translation is created
                    not page_translation_id
                    or
                    # slug has changed
                    PageTranslation.objects.get(id=page_translation_id).slug != slug
                )
                and
                # the new slug already exists
                PageTranslation.objects.filter(slug=slug).exists()
        ):
            old_slug = slug
            i = 1
            while True:
                i += 1
                slug = old_slug + '-' + str(i)
                if not PageTranslation.objects.filter(slug=slug).exists():
                    break

        # TODO: version, active_version
        if page_translation_id:
            page_object = PageTranslation.objects.filter(
                id=page_translation_id).select_related('page').first()

            # save page
            page = Page.objects.get(id=page_object.page.id)
            page.icon = self.cleaned_data['icon']
            page.save()
            page.move_to(self.cleaned_data['parent'], self.cleaned_data['position'])

            # save page translation
            page_translation = PageTranslation.objects.get(id=page_object.id)
            page_translation.slug = slug
            page_translation.title = self.cleaned_data['title']
            page_translation.text = self.cleaned_data['text']
            page_translation.status = self.cleaned_data['status']
            page_translation.language = self.cleaned_data['language']
            page_translation.save()
        else:
            # create page
            page = Page.objects.create(
                icon=self.cleaned_data['icon'],
                site=Site.objects.get(slug=site_slug),
            )
            page.move_to(self.cleaned_data['parent'], self.cleaned_data['position'])

            # create page translation
            page_translation = PageTranslation.objects.create(
                slug=slug,
                title=self.cleaned_data['title'],
                text=self.cleaned_data['text'],
                status=self.cleaned_data['status'],
                language=self.cleaned_data['language'],
                page=page,
                creator=self.user
            )
