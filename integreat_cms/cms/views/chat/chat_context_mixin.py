from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.views.generic.base import ContextMixin

from ...forms import ChatMessageForm
from ...models import ChatMessage

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class ChatContextMixin(ContextMixin):
    """
    This mixin provides the chat context for dashboard views (see :class:`~django.views.generic.base.ContextMixin`)
    """

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        context.update(self.get_chat_context_data())
        return context

    def get_chat_context_data(self) -> dict[str, Any]:
        """
        Returns the chat context variables ``chat_form``, ``chat_messages`` and ``chat_last_visited``.

        :return: The chat context
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
