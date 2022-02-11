"""
Custom user model that is used instead of the default Django user model
"""

import logging

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractUser, UserManager

from .organization import Organization
from ..chat.chat_message import ChatMessage
from ..regions.region import Region

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class CustomUserManager(UserManager):
    """
    This manager prefetches the regions of each user because they are needed for permissions checks and the region selection anyway
    """

    def get_queryset(self):
        """
        Get the queryset of users including the prefetched ``regions``

        :return: The queryset of users
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.users.user.User ]
        """
        return (
            super()
            .get_queryset()
            .prefetch_related(
                models.Prefetch(
                    "regions", queryset=Region.objects.order_by("-last_updated")
                )
            )
        )


class User(AbstractUser):
    """
    A custom User model that replaces the default Django User model
    """

    regions = models.ManyToManyField(
        Region,
        blank=True,
        related_name="users",
        verbose_name=_("regions"),
        help_text=_("The regions to which the user has access"),
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
        verbose_name=_("organization"),
        help_text=_(
            "This allows the user to edit and publish all pages for which the organisation is registered as the responsible organisation"
        ),
    )
    chat_last_visited = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.min),
        verbose_name=_("last chat visit date"),
        help_text=_("The date and time when the user did read the chat the last time"),
    )
    expert_mode = models.BooleanField(
        default=False,
        verbose_name=_("experienced user"),
        help_text=_(
            "Enable this option to show up additional features like XLIFF import/export, page filtering, mirrored pages, page-based permissions, Do-Not-Translate-Tag and recurring events"
        ),
    )
    page_tree_tutorial_seen = models.BooleanField(
        default=False,
        verbose_name=_("Page tree tutorial seen"),
        help_text=_(
            "Will be set to true once the user dismissed the page tree tutorial"
        ),
    )

    #: Custom model manager for user objects
    objects = CustomUserManager()

    @cached_property
    def role(self):
        """
        We refer to Django user groups as roles.

        :return: The role of this user
        :rtype: ~integreat_cms.cms.models.users.role.Role
        """
        groups = self.groups.all()
        if groups:
            # Assume users only have one group/role
            return groups[0].role
        return None

    @property
    def full_user_name(self):
        """
        Return the full name of the user. If either the first or the last name are present, return them, otherwise
        return the username.

        :return: The full name of the user
        :rtype: str
        """
        return self.get_full_name() or self.get_username()

    @property
    def unread_chat_messages(self):
        """
        Return all unread messages of this user

        :return: The unread messages of this user
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.chat.chat_message.ChatMessage ]
        """
        return ChatMessage.history.filter(sent_datetime__gt=self.chat_last_visited)

    def update_chat_last_visited(self):
        """
        Update the :attr:`~integreat_cms.cms.models.users.user.User.chat_last_visited` to the current time

        :return: the previous :attr:`~integreat_cms.cms.models.users.user.User.chat_last_visited` value
        :rtype: ~datetime.datetime
        """
        previous_chat_last_visited = self.chat_last_visited
        self.chat_last_visited = timezone.now()
        self.save()
        logger.debug(
            "Field chat_last_visited of %r updated from %s to %s",
            self,
            previous_chat_last_visited.strftime("%Y-%m-%d %H:%M:%S"),
            self.chat_last_visited.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return previous_chat_last_visited

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``User object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the user
        :rtype: str
        """
        return self.full_user_name

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<User: User object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the user
        :rtype: str
        """
        optional_fields = ""
        if not self._state.adding:
            if self.is_staff:
                if self.role:
                    optional_fields += f", team: {self.role.english_name}"
                if self.is_superuser:
                    optional_fields += ", superuser"
                else:
                    optional_fields += ", staff"
            else:
                if self.role:
                    optional_fields += f", role: {self.role.english_name}"
                regions = self.regions.all()
                if len(regions) == 1:
                    optional_fields += f", region: {regions[0].name}"
        return f"<User (id: {self.id}, username: {self.username}{optional_fields})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("user")
        #: The plural verbose name of the model
        verbose_name_plural = _("users")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
