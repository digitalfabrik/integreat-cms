from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel

# pylint: disable=too-few-public-methods
class ChatHistoryManager(models.Manager):
    """
    Custom manager for returning the chat history of the last x days
    (as configured in :attr:`~integreat_cms.core.settings.AUTHOR_CHAT_HISTORY_DAYS`)
    """

    def get_queryset(self):
        """
        Custom queryset with applied filters to return the chat messages of the last x days

        :return: The QuerySet of the most recent chat history
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.chat.chat_message.ChatMessage ]
        """
        return (
            super()
            .get_queryset()
            .filter(
                sent_datetime__gt=timezone.now()
                - timezone.timedelta(days=settings.AUTHOR_CHAT_HISTORY_DAYS)
            )
        )


class ChatMessage(AbstractBaseModel):
    """
    A model for a message in the author chat
    """

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        verbose_name=_("sender"),
    )
    text = models.TextField(verbose_name=_("content"))
    sent_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("sent date"),
    )

    #: The default manager
    objects = models.Manager()
    #: A manager for the most recent chat history
    history = ChatHistoryManager()

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``ChatMessage object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the chat message
        :rtype: str
        """
        return f"{self.sent_datetime.strftime('%Y-%m-%d %H:%M')} - {self.sender.full_user_name}: {self.text}"

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<ChatMessage: ChatMessage object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the chat message
        :rtype: str
        """
        return f"<ChatMessage (id: {self.id}, sender: {self.sender.username}, date: {self.sent_datetime.strftime('%Y-%m-%d %H:%M')})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("chat message")
        #: The plural verbose name of the model
        verbose_name_plural = _("chat messages")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["-sent_datetime"]
        #: The default permissions for this model
        default_permissions = ("delete", "change")
