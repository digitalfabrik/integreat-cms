import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from treebeard.forms import MoveNodeForm

from ...constants import mirrored_page_first, position
from ...models import Page, Region
from ..custom_model_form import CustomModelForm
from ..icon_widget import IconWidget
from .parent_field_widget import ParentFieldWidget

logger = logging.getLogger(__name__)


class PageForm(CustomModelForm, MoveNodeForm):
    """
    Form for creating and modifying page objects
    """

    parent = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        required=False,
        widget=ParentFieldWidget(),
        label=capfirst(Page._meta.get_field("parent").verbose_name),
    )
    editors = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        label=_("Editors"),
        help_text=_(
            "These users can edit this page, but are not allowed to publish it."
        ),
    )
    publishers = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        label=_("Publishers"),
        help_text=_("These users can edit and publish this page."),
    )
    mirrored_page_region = forms.ModelChoiceField(
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
        #: The widgets for the fields if they differ from the standard widgets
        widgets = {
            "mirrored_page_first": forms.Select(choices=mirrored_page_first.CHOICES),
            "icon": IconWidget(),
        }

    def __init__(self, **kwargs):
        r"""
        Initialize page form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """

        # Instantiate CustomModelForm
        super().__init__(**kwargs)

        # Hide tree node inputs
        self.fields["_ref_node_id"].widget = forms.HiddenInput()
        self.fields["_position"].widget = forms.HiddenInput()

        # pass form object to ParentFieldWidget
        self.fields["parent"].widget.form = self

        if "data" in kwargs:
            # dirty hack to remove fields when submitted by POST
            del self.fields["editors"]
            del self.fields["publishers"]
        else:
            # update the querysets otherwise
            self.fields["editors"].queryset = self.get_editor_queryset()
            self.fields["publishers"].queryset = self.get_publisher_queryset()

        # limit possible parents to pages of current region
        parent_queryset = self.instance.region.pages

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
            descendant_ids = [
                descendant.id
                for descendant in self.instance.get_cached_descendants(
                    include_self=True
                )
            ]
            parent_queryset = parent_queryset.exclude(id__in=descendant_ids)
            self.fields["parent"].initial = self.instance.parent
            # Exclude the current page from the possible options for mirrored pages
            self.fields["mirrored_page"].queryset = self.fields[
                "mirrored_page"
            ].queryset.exclude(id=self.instance.id)
        else:
            last_root_page = self.instance.region.get_root_pages().last()
            if last_root_page:
                self.fields["_ref_node_id"].initial = last_root_page.id
                self.fields["_position"].initial = position.RIGHT
            else:
                self.fields["_ref_node_id"].initial = 0
                self.fields["_position"].initial = position.FIRST_CHILD

        self.fields["parent"].queryset = parent_queryset

    def _clean_cleaned_data(self):
        """
        Delete auxiliary fields not belonging to node model and include instance attributes in cleaned_data

        :return: The initial data for _ref_node_id and _position fields
        :rtype: tuple
        """
        del self.cleaned_data["mirrored_page_region"]
        # This workaround is required because the MoveNodeForm does not take
        # instance attribute into account which are not included in cleaned_data
        self.cleaned_data["region"] = self.instance.region
        return super()._clean_cleaned_data()

    def get_editor_queryset(self):
        """
        This method retrieves all users, who are eligible to be defined as page editors because they don't yet have the
        permission to edit this page.

        :return: All potential page editors
        :rtype: ~django.db.models.query.QuerySet [ ~django.contrib.auth.models.User ]
        """

        permission_edit_page = Permission.objects.get(codename="change_page")
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

        permission_publish_page = Permission.objects.get(codename="publish_page")
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
