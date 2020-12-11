import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ugettext as _, get_language

from ...constants import position
from ...models import Page, Region


logger = logging.getLogger(__name__)


class ParentFieldWidget(forms.widgets.Select):
    """
    This Widget class is used to append the url for retrieving the page order tables to the data attributes of the options
    """

    form = None

    # pylint: disable=too-many-arguments
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if not value:
            value = 0
        if self.form.instance.id:
            option_dict["attrs"]["data-url"] = reverse(
                "get_page_order_table_ajax",
                kwargs={
                    "region_slug": self.form.region.slug,
                    "page_id": self.form.instance.id,
                    "parent_id": value,
                },
            )
        else:
            option_dict["attrs"]["data-url"] = reverse(
                "get_new_page_order_table_ajax",
                kwargs={
                    "region_slug": self.form.region.slug,
                    "parent_id": value,
                },
            )
        return option_dict


class ParentField(forms.ModelChoiceField):
    """
    Form field helper class to overwrite the label function (which would otherwise call __str__)
    """

    language = None

    # pylint: disable=arguments-differ
    def label_from_instance(self, page):
        label = " 🡒 ".join(
            [
                page.get_first_translation([get_language(), self.language.code]).title
                for page in page.get_ancestors(include_self=True)
            ]
        )
        logger.debug("Label for page %s: %s", page, label)
        return label


class MirrorPageField(forms.ModelChoiceField):
    """
    Form field helper class to show ancestors page titles in mirror page select
    """

    # pylint: disable=arguments-differ
    def label_from_instance(self, page):
        return " -> ".join(
            [
                page_iter.best_language_title()
                for page_iter in page.get_ancestors(include_self=True)
            ]
        )


class PageForm(forms.ModelForm):
    """
    Form for creating and modifying page objects
    """

    parent = ParentField(
        queryset=Page.objects.all(), required=False, widget=ParentFieldWidget()
    )
    related_page = forms.ModelChoiceField(
        queryset=Page.objects.all(), required=False, widget=forms.HiddenInput()
    )
    position = forms.ChoiceField(
        choices=position.CHOICES,
        initial=position.LAST_CHILD,
        widget=forms.HiddenInput(),
    )
    editors = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(), required=False
    )
    publishers = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(), required=False
    )
    mirrored_page_region = forms.ModelChoiceField(
        queryset=Region.objects.all(), required=False
    )
    mirrored_page = MirrorPageField(queryset=Page.objects.all(), required=False)
    TRUE_FALSE_CHOICES = (
        (True, _("Embed mirrored page before this page")),
        (False, _("Embed mirrored page after this page")),
    )
    mirrored_page_first = forms.BooleanField(
        widget=forms.Select(choices=TRUE_FALSE_CHOICES), required=False, initial=True
    )

    class Meta:
        model = Page
        fields = ["icon"]

    def __init__(self, *args, **kwargs):

        logger.info(
            "New PageForm instantiated with args %s and kwargs %s", args, kwargs
        )

        # pop kwarg to make sure the super class does not get this param
        self.region = kwargs.pop("region", None)
        language = kwargs.pop("language", None)
        disabled = kwargs.pop("disabled", None)

        # instantiate ModelForm
        super().__init__(*args, **kwargs)

        # pass form object to ParentFieldWidget
        self.fields["parent"].widget.form = self

        # If form is disabled because the user has no permissions to edit the page, disable all form fields
        if disabled:
            for _, field in self.fields.items():
                field.disabled = True

        if len(args) == 1:
            # dirty hack to remove fields when submitted by POST
            del self.fields["editors"]
            del self.fields["publishers"]
        else:
            # update the querysets otherwise
            self.fields["editors"].queryset = self.get_editor_queryset()
            self.fields["publishers"].queryset = self.get_publisher_queryset()

        # limit possible parents to pages of current region
        parent_queryset = self.region.pages

        # check if instance of this form already exists
        if self.instance.id:
            # remove children from possible parents
            children = self.instance.get_descendants(include_self=True)
            parent_queryset = parent_queryset.exclude(id__in=children)
            self.fields["parent"].initial = self.instance.parent
            # check if instance has siblings
            previous_sibling = self.instance.get_previous_sibling()
            next_sibling = self.instance.get_next_sibling()
            if previous_sibling:
                self.fields["related_page"].initial = previous_sibling
                self.fields["position"].initial = position.RIGHT
            elif next_sibling:
                self.fields["related_page"].initial = next_sibling
                self.fields["position"].initial = position.LEFT
            else:
                self.fields["related_page"].initial = self.instance.parent
                self.fields["position"].initial = position.LAST_CHILD

        self.mirrored_page = forms.ModelChoiceField(
            queryset=Page.objects.all(), required=False
        )

        if self.instance.mirrored_page:
            self.fields["mirrored_page"].queryset = Page.objects.filter(
                region=self.instance.mirrored_page.region
            )
            self.fields["mirrored_page"].initial = self.instance.mirrored_page
            self.fields[
                "mirrored_page_first"
            ].initial = self.instance.mirrored_page_first
            self.fields[
                "mirrored_page_region"
            ].initial = self.instance.mirrored_page.region

        # add the language to the parent field to make sure the translated page titles are shown
        self.fields["parent"].language = language
        self.fields["parent"].queryset = parent_queryset

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):

        logger.debug(
            "PageForm saved with args %s, kwargs %s, cleaned data %s and changed data %s",
            args,
            kwargs,
            self.cleaned_data,
            self.changed_data,
        )

        # don't commit saving of ModelForm, because required fields are still missing
        kwargs["commit"] = False
        page = super().save(*args, **kwargs)

        if not self.instance.id:
            # only update these values when page is created
            page.region = self.region
        page.archived = bool(self.data.get("submit_archive"))
        page.mirrored_page = self.cleaned_data["mirrored_page"]
        page.save()
        page.move_to(self.cleaned_data["related_page"], self.cleaned_data["position"])

        return page

    def get_editor_queryset(self):
        permission_edit_page = Permission.objects.get(codename="edit_pages")
        users_without_permissions = get_user_model().objects.exclude(
            Q(groups__permissions=permission_edit_page)
            | Q(user_permissions=permission_edit_page)
            | Q(is_superuser=True)
        )
        if self.instance.id:
            users_without_permissions = users_without_permissions.difference(
                self.instance.editors.all()
            )
        return users_without_permissions

    def get_publisher_queryset(self):
        permission_publish_page = Permission.objects.get(codename="publish_pages")
        users_without_permissions = get_user_model().objects.exclude(
            Q(groups__permissions=permission_publish_page)
            | Q(user_permissions=permission_publish_page)
            | Q(is_superuser=True)
        )
        if self.instance.id:
            users_without_permissions = users_without_permissions.difference(
                self.instance.publishers.all()
            )
        return users_without_permissions
