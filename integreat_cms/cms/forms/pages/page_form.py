from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.query import QuerySet

from django.utils.translation import gettext_lazy as _

from ...constants import mirrored_page_first, position
from ...models import Page, Region
from ..custom_model_form import CustomModelForm
from ..custom_tree_node_form import CustomTreeNodeForm
from ..icon_widget import IconWidget
from .mirrored_page_field_widget import MirroredPageFieldWidget
from .parent_field_widget import ParentFieldWidget

logger = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class PageForm(CustomModelForm, CustomTreeNodeForm):
    """
    Form for creating and modifying page objects
    """

    authors = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        label=_("Authors"),
        help_text=_(
            "These users can edit this page, but are not allowed to publish it."
        ),
    )
    editors = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        label=_("Editors"),
        help_text=_("These users can edit and publish this page."),
    )
    mirrored_page_region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        label=_("Source region for live content"),
    )
    enable_api_token = forms.BooleanField(
        required=False,
        label=_("Enable write access via API for this page"),
    )

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Page
        #: The fields of the model which should be handled by this form
        fields = [
            "icon",
            "mirrored_page",
            "mirrored_page_first",
            "organization",
            "parent",
            "api_token",
            "hix_ignore",
            "embedded_offers",
        ]
        #: The widgets for the fields if they differ from the standard widgets
        widgets = {
            "mirrored_page_first": forms.Select(choices=mirrored_page_first.CHOICES),
            "mirrored_page": MirroredPageFieldWidget(),
            "icon": IconWidget(),
            "parent": ParentFieldWidget(),
            "embedded_offers": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize page form

        :param \**kwargs: The supplied keyword arguments
        """

        # Instantiate CustomModelForm and CustomTreeNodeForm
        super().__init__(**kwargs)

        # Pass form object to ParentFieldWidget
        self.fields["parent"].widget.form = self
        self.fields["mirrored_page"].widget.form = self

        # The api token field should not be edited manually
        self.fields["api_token"].widget.attrs["readonly"] = True
        self.fields["enable_api_token"].initial = bool(self.instance.api_token)

        # Limit possible parents to pages of current region
        parent_queryset = self.instance.region.pages.all()

        # Set the initial value for the mirrored page region
        if self.instance.mirrored_page:
            self.fields["mirrored_page_region"].initial = (
                self.instance.mirrored_page.region_id
            )

        # Let mirrored page queryset be empty per default and only fill it if a region is selected
        mirrored_page_queryset = Page.objects.none()

        # Filter the offer providers available for embedding
        self.fields["embedded_offers"].queryset = self.instance.region.offers.filter(
            supported_by_app_in_content=True
        )

        # Filter Zammad forms out if the region has no Zammad-URL set
        if not self.instance.region.zammad_url:
            self.fields["embedded_offers"].queryset = self.fields[
                "embedded_offers"
            ].queryset.filter(is_zammad_form=False)

        if self.is_bound:
            # If form is bound (submitted with data) limit the queryset to the selected region to validate the selected
            # mirrored page and to render the options for the mirrored page.
            # If no region was selected, allow no mirrored page
            if mirrored_page_region := self.data["mirrored_page_region"]:
                mirrored_page_queryset = Region.objects.get(
                    id=mirrored_page_region
                ).pages.all()
            # Dirty hack to remove fields when submitted by POST (since they are handles by AJAX)
            del self.fields["authors"]
            del self.fields["editors"]
        else:
            # If form is unbound (rendered without data), set the initial queryset to the pages of the initial region
            # to render the options for the mirrored page
            if self.instance.mirrored_page:
                mirrored_page_queryset = self.instance.mirrored_page.region.pages.all()
            # Update the querysets otherwise
            self.fields["authors"].queryset = self.get_author_queryset()
            self.fields["editors"].queryset = self.get_editor_queryset()

        # Check if instance of this form already exists
        if self.instance.id:
            # Remove descendants from possible parents
            parent_queryset = parent_queryset.exclude(
                tree_id=self.instance.tree_id,
                lft__range=(self.instance.lft, self.instance.rgt - 1),
            )
            # Exclude the current page from the possible options for mirrored pages
            mirrored_page_queryset = mirrored_page_queryset.exclude(id=self.instance.id)
        else:
            # Set the default position to the right of the last root page
            if last_root_page := self.instance.region.get_root_pages().last():
                self.fields["_ref_node_id"].initial = last_root_page.id
                self.fields["_position"].initial = position.RIGHT
            else:
                # If no page exists, treebeard expects the value "" as reference node id
                self.fields["_ref_node_id"].initial = ""
                self.fields["_position"].initial = position.FIRST_CHILD

        # Set choices of mirrored_page field manually to make use of cache_tree()
        logger.debug("Set choices for mirrored page field:")
        self.fields["mirrored_page"].choices = [
            (page.id, str(page))
            for page in mirrored_page_queryset.cache_tree(archived=False)
        ]

        # Set choices of organizations manually to filter only organizations of the region of the page
        self.fields["organization"].queryset = self.instance.region.organizations.all()

        # Set choices of parent and _ref_node_id fields manually to make use of cache_tree()
        logger.debug("Set choices for parent field:")
        cached_parent_choices = [("", "---------")]
        cached_parent_choices.extend(
            [
                (page.id, str(page))
                for page in parent_queryset.cache_tree(archived=False)
            ]
        )
        ref_node_choices = [("", "---------")]
        ref_node_choices.extend(
            [(page.id, str(page)) for page in parent_queryset.cache_tree()]
        )
        self.fields["parent"].choices = cached_parent_choices
        self.fields["_ref_node_id"].choices = ref_node_choices

    def _clean_cleaned_data(self) -> tuple[str, int]:
        """
        Delete auxiliary fields not belonging to node model and include instance attributes in cleaned_data

        :return: The initial data for _ref_node_id and _position fields
        """
        del self.cleaned_data["mirrored_page_region"]
        del self.cleaned_data["enable_api_token"]
        return super()._clean_cleaned_data()

    def get_author_queryset(self) -> QuerySet:
        """
        This method retrieves all users, who are eligible to be defined as page authors because they don't yet have the
        permission to edit this page.

        :return: All potential page authors
        """

        users_without_permissions = (
            get_user_model()
            .objects.filter(
                regions=self.instance.region,
                is_superuser=False,
                is_staff=False,
                groups__permissions__codename="view_page",
            )
            .exclude(
                Q(groups__permissions__codename="change_page")
                | Q(user_permissions__codename="change_page")
                | Q(editable_pages=self.instance)
                | Q(publishable_pages=self.instance)
            )
        )
        if self.instance.id:
            users_without_permissions = users_without_permissions.difference(
                self.instance.authors.all()
            )
        return users_without_permissions

    def get_editor_queryset(self) -> QuerySet:
        """
        This method retrieves all users, who are eligible to be defined as page editors because they don't yet have
        the permission to publish this page.

        :return: All potential page editors
        """

        users_without_permissions = (
            get_user_model()
            .objects.filter(
                regions=self.instance.region,
                is_superuser=False,
                is_staff=False,
                groups__permissions__codename="view_page",
            )
            .exclude(
                Q(groups__permissions__codename="publish_page")
                | Q(user_permissions__codename="publish_page")
                | Q(publishable_pages=self.instance)
            )
        )
        if self.instance.id:
            users_without_permissions = users_without_permissions.difference(
                self.instance.editors.all()
            )
        return users_without_permissions
