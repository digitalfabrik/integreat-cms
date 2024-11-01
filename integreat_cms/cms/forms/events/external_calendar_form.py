from __future__ import annotations

from typing import TYPE_CHECKING

from ...models import ExternalCalendar
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any

    from ...models import User


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
        fields = ["name", "url", "import_filter_category"]

    def __init__(self, user: User | None, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not self.instance.created_by:
            self.instance.created_by = user
        self.instance.last_changed_by = user
