import logging
from collections import defaultdict

from django import forms
from django.utils.translation import gettext_lazy as _

from ...models import Region
from ..custom_model_form import CustomModelForm


logger = logging.getLogger(__name__)


class CustomCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Custom CheckboxSelectMultiple child class which appends a machine
    translation provider to option labels or disables them if no provider
    is available
    """

    #: The template to use when rendering this widget
    template_name = "translations/languages_input.html"


class TranslationsManagementForm(CustomModelForm):
    """
    Form for modifying machine translation settings of a region
    """

    machine_translatable_languages = forms.ModelMultipleChoiceField(
        widget=CustomCheckboxSelectMultiple(),
        queryset=None,
        required=False,
        label=_("Language Selection"),
        help_text=_("Allow machine translations into the following languages:"),
    )

    #: The languages that cannot be selected at the moment
    unavailable_languages = []

    class Meta:
        """
        This class contains additional meta configuration of the form class,
        see the :class:`django.forms.ModelForm` for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Region
        #: The fields of the model which should be handled by this form
        fields = [
            "machine_translate_pages",
            "machine_translate_events",
            "machine_translate_pois",
        ]

    def __init__(self, *args, **kwargs):
        r"""
        Initialize translations management form

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        super().__init__(*args, **kwargs)

        # Exclude inactive languages and the root node
        languages = self.instance.language_tree_nodes.filter(
            active=True, parent__isnull=False
        )
        mt_providers = defaultdict(list)
        self.unavailable_languages = []
        for language in languages:
            if language.mt_provider:
                mt_providers[language.mt_provider].append(
                    (language.id, language.translated_name)
                )
            else:
                self.unavailable_languages.append(language.translated_name)
        self.fields["machine_translatable_languages"].choices = mt_providers.items()
        self.fields["machine_translatable_languages"].queryset = languages.filter(
            id__in=[id for languages in mt_providers.values() for id, _ in languages]
        )
        self.initial[
            "machine_translatable_languages"
        ] = self.instance.language_tree_nodes.filter(machine_translation_enabled=True)

    def save(self, commit=True):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :type commit: bool

        :return: The saved region object
        :rtype: ~integreat_cms.cms.models.regions.region.Region
        """

        # Save CustomModelForm
        region = super().save(commit=commit)

        # Iterate over all machine translatable languages and toggle them based on the checkbox value
        for language in self.fields["machine_translatable_languages"].queryset:
            language.machine_translation_enabled = (
                language in self.cleaned_data["machine_translatable_languages"]
            )
            language.save()

        return region
