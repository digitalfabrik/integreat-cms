from __future__ import annotations

from ...models import ExternalCalendar
from ..custom_model_form import CustomModelForm


class ExternalCalendarForm(CustomModelForm):
    """
    Form for adding a new external calendar
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = ExternalCalendar
        #: The fields of the model which should be handled by this form
        fields = ["name", "url", "import_filter_tag"]
