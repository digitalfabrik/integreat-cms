import logging

from django.conf import settings
from django.db import models
from django.utils import timezone

from .organization import Organization
from ..chat.chat_message import ChatMessage
from ..regions.region import Region

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """
    Data model representing a user profile

    :param id: The database id of the user profile

    Relationship fields:

    :param user: The user this profile belongs to (related name: ``profile``)
    :param regions: The regions of this user (related name: ``users``)
    :param organization: The organization of the user (related name: ``members``)
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE
    )
    regions = models.ManyToManyField(Region, related_name="users", blank=True)
    organization = models.ForeignKey(
        Organization,
        related_name="members",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    chat_last_visited = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.min),
        verbose_name="Date and time of last chat visit",
        help_text="The date and time when the user did read the chat the last time",
    )
    expert_mode = models.BooleanField(default=False)

    @property
    def roles(self):
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
        Update the :attr:`cms.models.users.user_profile.chat_last_visited` to the current time

        :return: Return the previous :attr:`cms.models.users.user_profile.chat_last_visited` value
        :rtype: ~datetime.datetime
        """
        previous_chat_last_visited = self.chat_last_visited
        self.chat_last_visited = timezone.now()
        self.save()
        logger.debug(
            "Field chat_last_visited of user %s updated from %s to %s",
            self.user,
            previous_chat_last_visited,
            self.chat_last_visited,
        )
        return previous_chat_last_visited

    def __str__(self):
        return self.user.username

    class Meta:
        default_permissions = ()
        permissions = (
            ("manage_admin_users", "Can manage admin users"),
            ("manage_region_users", "Can manage region users"),
        )
