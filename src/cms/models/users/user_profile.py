import logging

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .organization import Organization
from ..chat.chat_message import ChatMessage
from ..regions.region import Region

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """
    Data model representing a user profile
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("user"),
    )
    regions = models.ManyToManyField(
        Region,
        blank=True,
        related_name="user_profiles",
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

    @property
    def role(self):
        """
        We refer to Django user groups as roles.

        :return: The role of this user
        :rtype: ~cms.models.users.role.Role
        """
        if self.user.groups.exists():
            return self.user.groups.first().role
        return None

    @property
    def full_user_name(self):
        """
        Return the full name of the user. If either the first or the last name are present, return them, otherwise
        return the username.

        :return: The full name of the user
        :rtype: str
        """
        return self.user.get_full_name() or self.user.get_username()

    @property
    def unread_chat_messages(self):
        """
        Return all unread messages of this user

        :return: The unread messages of this user
        :rtype: ~django.db.models.query.QuerySet [ ~cms.models.chat.chat_message.ChatMessage ]
        """
        return ChatMessage.history.filter(sent_datetime__gt=self.chat_last_visited)

    def update_chat_last_visited(self):
        """
        Update the :attr:`cms.models.users.user_profile.UserProfile.chat_last_visited` to the current time

        :return: Return the previous :attr:`cms.models.users.user_profile.UserProfile.chat_last_visited` value
        :rtype: ~datetime.datetime
        """
        previous_chat_last_visited = self.chat_last_visited
        self.chat_last_visited = timezone.now()
        self.save()
        logger.debug(
            "Field chat_last_visited of %r updated from %s to %s",
            self.user.profile,
            previous_chat_last_visited.strftime("%Y-%m-%d %H:%M:%S"),
            self.chat_last_visited.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return previous_chat_last_visited

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``UserProfile object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the user profile
        :rtype: str
        """
        return self.full_user_name

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<UserProfile: UserProfile object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the user profile
        :rtype: str
        """
        optional_fields = ""
        if self.user.is_staff:
            if self.role:
                optional_fields += f", team: {self.role.english_name}"
            if self.user.is_superuser:
                optional_fields += ", superuser"
            else:
                optional_fields += ", staff"
        else:
            if self.role:
                optional_fields += f", role: {self.role.english_name}"
            if self.regions.count() == 1:
                optional_fields += f", region: {self.regions.first().name}"
        return f"<UserProfile (id: {self.id}, username: {self.user.username}{optional_fields})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("user profile")
        #: The plural verbose name of the model
        verbose_name_plural = _("user profiles")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (
            ("manage_admin_users", "Can manage admin users"),
            ("manage_region_users", "Can manage region users"),
        )
