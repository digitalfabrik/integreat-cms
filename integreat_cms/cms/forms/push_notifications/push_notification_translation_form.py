import logging

from django.contrib import messages
from django.utils.translation import override, ugettext_lazy as _

from ..custom_model_form import CustomModelForm
from ...models import PushNotificationTranslation

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
        model = PushNotificationTranslation
        #: The fields of the model which should be handled by this form
        fields = ["title", "text", "language"]

    def add_error_messages(self, request):
        """
        This function overwrites :meth:`~integreat_cms.cms.forms.custom_model_form.CustomModelForm.add_error_messages`
        to add the language of the current translation to the error messages

        :param request: The current request submitting the form
        :type request: ~django.http.HttpRequest
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
