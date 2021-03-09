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
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
        verbose_name=_("organization"),
    )
    chat_last_visited = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.min),
        verbose_name=_("last chat visit date"),
        help_text=_("The date and time when the user did read the chat the last time"),
    )
    expert_mode = models.BooleanField(
        default=False,
        verbose_name=_("expert mode"),
        help_text=_(
            "Enable this option to show up additional features like XLIFF import/export, page filtering, mirrored pages, page-based permissions, Do-Not-Translate-Tag and recurring events"
        ),
    )

    @property
    def roles(self):
        """
        We refer to Django user groups as roles.

        :return: The roles/groups of this user
        :rtype: ~django.db.models.query.QuerySet [ ~django.contrib.auth.models.Group ]
        """
        return self.user.groups.all()

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
            previous_chat_last_visited.strftime("%Y-%m-%d %H:%M:%r"),
            self.chat_last_visited.strftime("%Y-%m-%d %H:%M:%r"),
        )
        return previous_chat_last_visited

    def __str__(self):
        """
        The string representation of this user profile

        :return: THe username
        :rtype: str
        """
        return self.user.username

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
