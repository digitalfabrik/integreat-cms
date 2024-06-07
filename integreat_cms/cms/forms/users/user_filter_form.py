from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH

if TYPE_CHECKING:
    from django.db.models.query import QuerySet

    from ...models import User

from django.utils.translation import gettext_lazy as _

from ...constants import roles
from ...models import Region
from ...utils.user_utils import search_users
from ..custom_filter_form import CustomFilterForm

logger = logging.getLogger(__name__)


class UserFilterForm(CustomFilterForm):
    """
    Form for filtering user objects
    """

    role = forms.ChoiceField(
        label=_("Role"),
        choices=BLANK_CHOICE_DASH + roles.CHOICES,
        required=False,
    )
    permissions = forms.ChoiceField(
        label=_("Permissions"),
        choices=BLANK_CHOICE_DASH
        + [
            ("is_superuser", _("Administrator")),
            ("is_staff", _("Integreat team member")),
        ],
        required=False,
    )
    region = forms.ModelChoiceField(
        label=_("Region"),
        queryset=Region.objects.all(),
        required=False,
    )
    query = forms.CharField(required=False)

    def apply(self, users: QuerySet[User]) -> QuerySet[User]:
        """
        Filter the users list according to the given filter data

        :param users: The list of users
        :return: The filtered page list
        """
        if self.is_enabled:
            logger.debug("User list filtered with changed data %r", self.changed_data)
            if "query" in self.changed_data:
                users = self.filter_by_query(users)
            if "role" in self.changed_data:
                users = users.filter(groups__name=self.cleaned_data["role"])
            if "permissions" in self.changed_data:
                users = users.filter(**{self.cleaned_data["permissions"]: True})
            if "region" in self.changed_data:
                users = users.filter(regions=self.cleaned_data["region"])
        return users

    def filter_by_query(self, users: QuerySet[User]) -> QuerySet[User]:
        """
        Filter the pages list by a given search query

        :param users: The list of users
        :return: The filtered page list
        """
        query = self.cleaned_data["query"].lower()
        user_keys = search_users(region=None, query=query).values("pk")
        users = users.filter(pk__in=user_keys)
        return users
