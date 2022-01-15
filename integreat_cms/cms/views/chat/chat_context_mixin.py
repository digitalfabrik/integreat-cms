import logging

from django.views.generic.base import ContextMixin

from ...forms import ChatMessageForm
from ...models import ChatMessage

logger = logging.getLogger(__name__)


class ChatContextMixin(ContextMixin):
    """
    This mixin provides the chat context for dashboard views (see :class:`~django.views.generic.base.ContextMixin`)
    """

    def get_context_data(self, **kwargs):
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context.update(self.get_chat_context_data())
        return context

    def get_chat_context_data(self):
        """
        Returns the chat context variables ``chat_form``, ``chat_messages`` and ``chat_last_visited``.

        :return: The chat context
        :rtype: dict
        """
        region = self.request.region

        if region and not region.chat_enabled:
            logger.debug("Chat in %r is disabled", region)
            return {}

        return {
            "chat_form": ChatMessageForm(),
            "chat_messages": ChatMessage.history.all(),
            "chat_last_visited": self.request.user.update_chat_last_visited(),
        }
