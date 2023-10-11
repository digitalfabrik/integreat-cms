from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from ...constants import push_notifications
from ...models import PushNotificationTranslation
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from django.db.models.base import ModelBase
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


class PushNotificationTranslationForm(CustomModelForm):
    """
    Form for creating and modifying push notification translation objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model: ModelBase = PushNotificationTranslation
        #: The fields of the model which should be handled by this form
        fields: list[str] = ["title", "text", "language"]

    def add_error_messages(self, request: HttpRequest) -> None:
        """
        This function overwrites :meth:`~integreat_cms.cms.forms.custom_model_form.CustomModelForm.add_error_messages`
        to add the language of the current translation to the error messages

        :param request: The current request submitting the form
        """
        # Add field errors
        for field in self:
            for error in field.errors:
                messages.error(
                    request,
                    f"{_(field.label)} ({self.instance.language.translated_name}): {_(error)}",
                )
        # Add non-field errors
        for error in self.non_field_errors():
            messages.error(
                request, f"{self.instance.language.translated_name}: {_(error)}"
            )
        # Add debug logging in english
        with override("en"):
            logger.debug(
                "PushNotificationTranslationForm submitted with errors: %r", self.errors
            )

    def has_changed(self) -> bool:
        """
        Return ``True`` if submitted data differs from initial data.
        If the main language should be used as fallback for missing translations, this always return ``True``.

        :return: Whether the form has changed
        """
        if (
            hasattr(self.instance, "push_notification")
            and self.instance.push_notification.mode
            == push_notifications.USE_MAIN_LANGUAGE
        ):
            return True
        return super().has_changed()
