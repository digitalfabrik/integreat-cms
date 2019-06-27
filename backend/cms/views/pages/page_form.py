"""
Form for creating a page object and page translation object
"""

import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from ...models import Page, PageTranslation
from ..general import POSITION_CHOICES


logger = logging.getLogger(__name__)


class ParentField(forms.ModelChoiceField):
    """
        Subclass of ModelChoiceField
        Helper to overwrite the label function (which would otherwise call __str__)
    """

    def label_from_instance(self, page):
        logger.info('Generate label for page with id {} in language {}'.format(page, self.language))
        return ' -> '.join([
            page.get_translation(self.language.code).title
            for page in page.get_ancestors(include_self=True)
        ])


class PageForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    position = forms.ChoiceField(choices=POSITION_CHOICES, initial=POSITION_CHOICES[0][0])
    parent = ParentField(queryset=Page.objects.all(), required=False)
    editors = forms.ModelChoiceField(queryset=get_user_model().objects.all(), required=False)
    publishers = forms.ModelChoiceField(queryset=get_user_model().objects.all(), required=False)

    class Meta:
        model = Page
        fields = ['icon']

    def __init__(self, *args, **kwargs):

        logger.info('New PageForm instantiated with args {} and kwargs {}'.format(args, kwargs))

        # pop kwarg to make sure the super class does not get this param
        self.site = kwargs.pop('site', None)
        language = kwargs.pop('language', None)

        # add initial kwarg to make sure changed_data is preserved
        kwargs['initial'] = {
            'position': POSITION_CHOICES[0][0]
        }

        # instantiate ModelForm
        super(PageForm, self).__init__(*args, **kwargs)

        if len(args) == 1:
            # dirty hack to remove fields when submitted by POST
            del self.fields['editors']
            del self.fields['publishers']
        else:
            # update the querysets otherwise
            self.fields['editors'].queryset = self.get_editor_queryset()
            self.fields['publishers'].queryset = self.get_publisher_queryset()

        # limit possible parents to pages of current region
        parent_queryset = Page.objects.filter(
            site=self.site,
        )
        # limit possible queryset to page which has translation in current language
        for parent in parent_queryset:
            if not parent.get_translation(language_code=language.code):
                parent_queryset = parent_queryset.exclude(id=parent.id)

        # check if instance of this form already exists
        if self.instance.id:
            # remove children from possible parents
            children = self.instance.get_descendants(include_self=True)
            parent_queryset = parent_queryset.exclude(id__in=children)
            self.fields['parent'].initial = self.instance.parent

        # add the language to the parent field to make sure the translated page titles are shown
        self.fields['parent'].language = language
        self.fields['parent'].queryset = parent_queryset


    def save(self, *args, **kwargs):

        logger.info('PageForm saved with args {} and kwargs {}'.format(args, kwargs))

        # don't commit saving of ModelForm, because required fields are still missing
        kwargs['commit'] = False
        page = super(PageForm, self).save(*args, **kwargs)

        if not self.instance.id:
            # only update these values when page is created
            page.site = self.site
        page.archived = bool(self.data.get('submit_archive'))
        page.save()
        page.move_to(self.cleaned_data['parent'], self.cleaned_data['position'])

        return page

    def get_editor_queryset(self):
        permission_edit_page = Permission.objects.get(codename='edit_pages')
        users_without_permissions = get_user_model().objects.exclude(
            Q(groups__permissions=permission_edit_page) |
            Q(user_permissions=permission_edit_page) |
            Q(is_superuser=True)
        )
        if self.instance.id:
            users_without_permissions = users_without_permissions.difference(self.instance.editors.all())
        return users_without_permissions

    def get_publisher_queryset(self):
        permission_publish_page = Permission.objects.get(codename='publish_pages')
        users_without_permissions = get_user_model().objects.exclude(
            Q(groups__permissions=permission_publish_page) |
            Q(user_permissions=permission_publish_page) |
            Q(is_superuser=True)
        )
        if self.instance.id:
            users_without_permissions = users_without_permissions.difference(self.instance.publishers.all())
        return users_without_permissions


class PageTranslationForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    PUBLIC_CHOICES = (
        (True, _('Public')),
        (False, _('Private')),
    )

    class Meta:
        model = PageTranslation
        fields = ['title', 'status', 'text', 'slug', 'public']

    def __init__(self, *args, **kwargs):

        logger.info('New PageTranslationForm with args {} and kwargs {}'.format(args, kwargs))

        # pop kwarg to make sure the super class does not get this param
        self.site = kwargs.pop('site', None)
        self.language = kwargs.pop('language', None)

        # to set the public value through the submit button, we have to overwrite the field value for public.
        # we could also do this in the save() function, but this would mean that it is not recognized in changed_data.
        # check if POST data was submitted and the publish button was pressed
        if len(args) == 1 and 'submit_publish' in args[0]:
            # copy QueryDict because it is immutable
            post = args[0].copy()
            # remove the old public value (might be False and update() does only append, not overwrite)
            post.pop('public')
            # update the POST field with True (has to be a string to make sure the field is recognized as changed)
            post.update({'public': 'True'})
            # set the args to POST again
            args = (post,)
            logger.info('changed POST arg public manually to True')

        super(PageTranslationForm, self).__init__(*args, **kwargs)

        self.fields['public'].widget = forms.Select(choices=self.PUBLIC_CHOICES)

    def save(self, *args, **kwargs):

        logger.info('PageTranslationForm saved with args {} and kwargs {}'.format(args, kwargs))

        # pop kwarg to make sure the super class does not get this param
        page = kwargs.pop('page', None)
        user = kwargs.pop('user', None)

        if not self.instance.id:
            # don't commit saving of ModelForm, because required fields are still missing
            kwargs['commit'] = False

        page_translation = super(PageTranslationForm, self).save(*args, **kwargs)

        if not self.instance.id:
            # only update these values when page translation is created
            page_translation.page = page
            page_translation.creator = user
            page_translation.language = self.language

        page_translation.save()

        return page_translation

    def clean_slug(self):

        slug = self.cleaned_data['slug']
        # if slug is empty, generate from title
        if not slug:
            # slugify to make sure slug doesn't contain special chars etc.
            slug = slugify(self.cleaned_data['title'])
            logger.info('Generate new slug from title {}'.format(slug))

        # make sure slug is unique per region and language
        unique_slug = slug
        i = 1
        while True:
            other_page_translation = PageTranslation.objects.filter(
                page__site=self.site,
                language=self.language,
                slug=unique_slug
            ).exclude(id=self.instance.id)
            if not other_page_translation.exists():
                break
            i += 1
            unique_slug = '{}-{}'.format(slug, i)

        if self.cleaned_data['slug'] != unique_slug:
            logger.info('Cleaned slug from {} to {}.'.format(self.cleaned_data['slug'], unique_slug))

        return unique_slug
