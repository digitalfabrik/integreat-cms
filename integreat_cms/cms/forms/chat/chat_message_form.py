from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ...models import ChatMessage
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class ChatMessageForm(CustomModelForm):
    """
    Form for submitting chat messages
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        model = ChatMessage
        fields = ["text"]

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize chat message form

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        """
        # pop kwarg to make sure the super class does not get this param
        sender = kwargs.pop("sender", None)

        super().__init__(**kwargs)

        self.instance.sender = sender
