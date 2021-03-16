import logging

from html import escape

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils.html import mark_safe
from django.utils.translation import ugettext as _, get_language
from django.utils.text import capfirst

from ...constants import position, region_status, mirrored_page_first
from ...models import Page, Region
from ..custom_model_form import CustomModelForm
from ..icon_widget import IconWidget
from .parent_field_widget import ParentFieldWidget


logger = logging.getLogger(__name__)


class ParentField(forms.ModelChoiceField):
    """
    Form field helper class to overwrite the label function (which would otherwise call __str__)
    """

    #: The language of this field
    language = None

    # pylint: disable=arguments-differ
    def label_from_instance(self, page):
        """
        Generate a label for the given page in the parent page select options

        :param page: The page which should be used as parent
        :type page: ~cms.models.pages.page.Page

        :return: The label for the given page
        :rtype: str
        """
        label = " &rarr; ".join(
            [
                # escape page title because string is marked as safe afterwards
                escape(
                    page.get_first_translation(
                        [get_language(), self.language.slug]
                    ).title
                )
                for page in page.get_ancestors(include_self=True)
            ]
        )
        logger.debug("Label for page %r: %r", page, label)
        # mark as safe so that the arrow is not escaped
        return mark_safe(label)


class MirrorPageField(forms.ModelChoiceField):
    """
    Form field helper class to show ancestors page titles in mirror page select
    """

    # pylint: disable=arguments-differ
    def label_from_instance(self, page):
        """
        Generate a label for the given page in the mirror page select options

        :param page: The page which should be mirrored
        :type page: ~cms.models.pages.page.Page

        :return: The label for the given page
        :rtype: str
        """
        label = " &rarr; ".join(
            [
                # escape page title because string is marked as safe afterwards
                escape(page_iter.backend_translation.title)
                for page_iter in page.get_ancestors(include_self=True)
            ]
        )
        # Add warning if page is archived
        if page.archived:
            label += " (&#9888; " + _("Archived") + ")"
        # mark as safe so that the arrow and the warning triangle are not escaped
        return mark_safe(label)


class MirroredPageRegionField(forms.ModelChoiceField):
    """
    Form field helper class to warnings if mirrored content comes from hidden or archived region
    """

    # pylint: disable=arguments-differ
    def label_from_instance(self, region):
        """
        Generate a label for the selected region in the mirror page select options

        :param region: The region from which a page should be mirrored
        :type region: ~cms.models.pages.page.Page

        :return: The label for the given region
        :rtype: str
        """
        label = escape(super().label_from_instance(region))
        if region.status == region_status.HIDDEN:
            # Add warning if region is hidden
            label += " (&#9888; " + _("Hidden") + ")"
        elif region.status == region_status.ARCHIVED:
            # Add warning if region is archived
            label += " (&#9888; " + _("Archived") + ")"
        # mark as safe so that the warning triangle is not escaped
        return mark_safe(label)


class PageForm(CustomModelForm):
    """
    Form for creating and modifying page objects
    """

    parent = ParentField(
        queryset=Page.objects.all(),
        required=False,
        widget=ParentFieldWidget(),
        label=capfirst(Page._meta.get_field("parent").verbose_name),
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
    mirrored_page_region = MirroredPageRegionField(
        queryset=Region.objects.all(), required=False
    )

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Page
        #: The fields of the model which should be handled by this form
        fields = ["icon", "mirrored_page", "mirrored_page_first", "organization"]
        #: The classes for the fields if they differ from the standard field class
        field_classes = {"mirrored_page": MirrorPageField}
        #: The widgets for the fields if they differ from the standard widgets
        widgets = {
            "mirrored_page_first": forms.Select(choices=mirrored_page_first.CHOICES),
            "icon": IconWidget(),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize page form

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict
        """

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

        # Set the initial value for the mirrored page region
        if self.instance.mirrored_page:
            self.fields[
                "mirrored_page_region"
            ].initial = self.instance.mirrored_page.region

        if self.is_bound:
            # If form is bound (submitted with data) limit the queryset to the selected region to validate the selected
            # mirrored page and to render the options for the mirrored page.
            # If no region was selected, allow no mirrored page
            mirrored_page_region = (
                self.data["mirrored_page_region"]
                if self.data["mirrored_page_region"]
                else None
            )
            self.fields["mirrored_page"].queryset = self.fields[
                "mirrored_page"
            ].queryset.filter(region=mirrored_page_region)
        else:
            # If form is unbound (rendered without data), set the initial queryset to the pages of the initial region
            # to render the options for the mirrored page
            self.fields["mirrored_page"].queryset = Page.objects.filter(
                region=self.fields["mirrored_page_region"].initial
            )

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
            # Exclude the current page from the possible options for mirrored pages
            self.fields["mirrored_page"].queryset = self.fields[
                "mirrored_page"
            ].queryset.exclude(id=self.instance.id)

        # add the language to the parent field to make sure the translated page titles are shown
        self.fields["parent"].language = language
        self.fields["parent"].queryset = parent_queryset

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The saved page object
        :rtype: ~cms.models.pages.page.Page
        """

        # don't commit saving of ModelForm, because required fields are still missing
        kwargs["commit"] = False
        page = super().save(*args, **kwargs)

        if not self.instance.id:
            # only update these values when page is created
            page.region = self.region
        page.save()
        page.move_to(self.cleaned_data["related_page"], self.cleaned_data["position"])

        return page

    def get_editor_queryset(self):
        """
        This method retrieves all users, who are eligible to be defined as page editors because they don't yet have the
        permission to edit this page.

        :return: All potential page editors
        :rtype: ~django.db.models.query.QuerySet [ ~django.contrib.auth.models.User ]
        """

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
        """
        This method retrieves all users, who are eligible to be defined as page publishers because they don't yet have
        the permission to publish this page.

        :return: All potential page publishers
        :rtype: ~django.db.models.query.QuerySet [ ~django.contrib.auth.models.User ]
        """

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
