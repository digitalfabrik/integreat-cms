from __future__ import annotations

from typing import TYPE_CHECKING

from ...constants import language_color
from ...models import Language
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any


class LanguageForm(CustomModelForm):
    """
    Form for creating and modifying language objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Language
        #: The fields of the model which should be handled by this form
        fields = [
            "slug",
            "bcp47_tag",
            "english_name",
            "native_name",
            "text_direction",
            "table_of_contents",
            "social_media_webapp_title",
            "social_media_webapp_description",
            "primary_country_code",
            "secondary_country_code",
            "language_color",
            "message_content_not_available",
            "message_partial_live_content_not_available",
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        r"""
        Initialize language form

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        """

        # Instantiate ModelForm
        super().__init__(*args, **kwargs)

        # Sort countries by translated name
        sorted_language_choices = sorted(
            self.fields["primary_country_code"].choices, key=lambda x: x[1]
        )
        self.fields["primary_country_code"].choices = sorted_language_choices
        self.fields["secondary_country_code"].choices = sorted_language_choices

        # Make the language color field required
        self.fields["language_color"].required = True

        # Show unused colors first in the list, after them used colors with the assigned language name
        used_colors = []
        unused_colors = []
        for color in language_color.COLORS:
            color_code, name = color
            if language := Language.objects.filter(language_color=color_code).first():
                modified_name = name + " (" + language.translated_name + ")"
                used_colors += [(color_code, modified_name)]
            else:
                unused_colors += [color]
        used_colors = sorted(used_colors, key=lambda x: x[1])
        unused_colors = sorted(unused_colors, key=lambda x: x[1])
        self.fields["language_color"].choices = unused_colors + used_colors

        if self.instance.language_color:
            self.fields["language_color"].initial = self.instance.language_color

        # Make left border rounded if no flag is selected yet
        if not self.instance.primary_country_code:
            self.fields["primary_country_code"].widget.attrs[
                "class"
            ] = "rounded-l border-l"
        if not self.instance.secondary_country_code:
            self.fields["secondary_country_code"].widget.attrs[
                "class"
            ] = "rounded-l border-l"
        if not self.instance.language_color:
            self.fields["language_color"].widget.attrs["class"] = "rounded-l border-l"
