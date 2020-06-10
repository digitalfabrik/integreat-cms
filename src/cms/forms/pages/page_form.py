"""
Form for creating a page object and page translation object
"""
import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils.translation import ugettext as _

from ...constants import position
from ...models import Page, Region


logger = logging.getLogger(__name__)


class ParentField(forms.ModelChoiceField):
    """
        Subclass of ModelChoiceField
        Helper to overwrite the label function (which would otherwise call __str__)
    """
    language = None

    # pylint: disable=arguments-differ
    def label_from_instance(self, page):
        logger.info(
            'Generate label for page with id %s in language %s',
            page,
            self.language
        )
        return ' -> '.join([
            page.get_first_translation([self.language.code]).title
            for page in page.get_ancestors(include_self=True)
        ])


class MirrorPageField(forms.ModelChoiceField):
    """
    Show ancestors page titles in mirror page select
    """

    # pylint: disable=arguments-differ
    def label_from_instance(self, page):
        return ' -> '.join([page_iter.best_language_title() for page_iter in page.get_ancestors(include_self=True)])


class PageForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    position = forms.ChoiceField(choices=position.CHOICES, initial=position.FIRST_CHILD)
    parent = ParentField(queryset=Page.objects.all(), required=False)
    editors = forms.ModelChoiceField(queryset=get_user_model().objects.all(), required=False)
    publishers = forms.ModelChoiceField(queryset=get_user_model().objects.all(), required=False)
    mirrored_page_region = forms.ModelChoiceField(queryset=Region.objects.all(), required=False)
    mirrored_page = MirrorPageField(queryset=Page.objects.all(), required=False)
    TRUE_FALSE_CHOICES = (
        (True, _('Embed mirrored page before this page')),
        (False, _('Embed mirrored page after this page'))
    )
    mirrored_page_first = forms.ChoiceField(choices=TRUE_FALSE_CHOICES,
                                            widget=forms.Select(),
                                            required=False)

    class Meta:
        model = Page
        fields = ['icon']

    def __init__(self, *args, **kwargs):

        logger.info(
            'New PageForm instantiated with args %s and kwargs %s',
            args,
            kwargs
        )

        # pop kwarg to make sure the super class does not get this param
        self.region = kwargs.pop('region', None)
        language = kwargs.pop('language', None)
        disabled = kwargs.pop('disabled', None)

        # add initial kwarg to make sure changed_data is preserved
        kwargs['initial'] = {
            'position': position.FIRST_CHILD
        }

        # instantiate ModelForm
        super(PageForm, self).__init__(*args, **kwargs)

        # If form is disabled because the user has no permissions to edit the page, disable all form fields
        if disabled:
            for _, field in self.fields.items():
                field.disabled = True

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
            region=self.region,
        )

        # check if instance of this form already exists
        if self.instance.id:
            # remove children from possible parents
            children = self.instance.get_descendants(include_self=True)
            parent_queryset = parent_queryset.exclude(id__in=children)
            self.fields['parent'].initial = self.instance.parent

        self.mirrored_page = forms.ModelChoiceField(queryset=Page.objects.all(), required=False)

        if self.instance.mirrored_page:
            self.fields['mirrored_page'].queryset = Page.objects.filter(region=self.instance.mirrored_page.region)
            self.fields['mirrored_page'].initial = self.instance.mirrored_page
            self.fields['mirrored_page_first'].initial = self.instance.mirrored_page_first
            self.fields['mirrored_page_region'].initial = self.instance.mirrored_page.region

        # add the language to the parent field to make sure the translated page titles are shown
        self.fields['parent'].language = language
        self.fields['parent'].queryset = parent_queryset


    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):

        logger.info(
            'PageForm saved with args %s and kwargs %s',
            args,
            kwargs
        )

        # don't commit saving of ModelForm, because required fields are still missing
        kwargs['commit'] = False
        page = super(PageForm, self).save(*args, **kwargs)

        if not self.instance.id:
            # only update these values when page is created
            page.region = self.region
        page.archived = bool(self.data.get('submit_archive'))
        page.mirrored_page = self.cleaned_data['mirrored_page']
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
