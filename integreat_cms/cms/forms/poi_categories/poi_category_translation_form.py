import logging

from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.forms.formsets import DELETION_FIELD_NAME
from django.utils.translation import gettext_lazy as _

from ...models import Language, POICategory, POICategoryTranslation
from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class POICategoryTranslationForm(CustomModelForm):
    """
    Form for creating and modifying POI category translation objects
    """

    def __init__(self, **kwargs):
        r"""
        Initialize POI category translation form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """

        # Instantiate CustomModelForm
        super().__init__(**kwargs)

        # Do not require category and name fields
        self.fields["category"].required = False
        self.fields["name"].required = False

        # Set custom language labels
        language_name = self.instance.language.translated_name
        self.fields["name"].widget.attrs.update(
            {"placeholder": _("Enter name in {} here").format(language_name)}
        )
        self.fields["name"].label = _("Translation in {}").format(language_name)

    def clean(self):
        """
        This method extends the ``clean()``-method to delete translations with an empty name.

        :return: The cleaned data (see :ref:`overriding-modelform-clean-method`)
        :rtype: dict
        """
        cleaned_data = super().clean()
        # If the name field is empty, delete the form
        if not cleaned_data.get("name") and "name" not in self.errors:
            cleaned_data[DELETION_FIELD_NAME] = True
        return cleaned_data

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = POICategoryTranslation
        #: The fields of the model which should be handled by this form
        fields = ["category", "language", "name"]


class BaseInlinePOICategoryTranslationFormSet(BaseInlineFormSet):
    """
    A formset for translations of POI categories
    """

    def get_form_kwargs(self, index):
        """
        Return additional keyword arguments for each individual formset form.
        (see :meth:`~django.views.generic.edit.ModelFormMixin.get_form_kwargs` and
        :ref:`django:custom-formset-form-kwargs`)

        :param index: The index of the initialized form
                      (will be ``None`` if the form being constructed is a new empty form)
        :type index: int

        :return: The form kwargs
        :rtype: dict
        """
        kwargs = super().get_form_kwargs(index)
        # Only add the additional instances for extra forms which do not have the initial data
        if index >= self.initial_form_count():
            # Get the relative index of all extra forms
            rel_index = index - self.initial_form_count()
            # Get all remaining languages
            languages = Language.objects.exclude(
                id__in=self.instance.translations.values_list("language__id", flat=True)
            )
            # Assign the language to the form with this index
            kwargs["additional_instance_attributes"] = {
                "language": languages[rel_index]
            }
        return kwargs

    def clean(self):
        """
        Make sure that at least one translation is given

        :raises ~django.core.exceptions.ValidationError: When not a single form contains a valid text
        """
        super().clean()
        if not any(form.cleaned_data.get("name") for form in self):
            raise ValidationError(_("At least one translation is required."))


def poi_category_translation_formset_factory():
    """
    Build the formset class

    :returns: The POICategoryTranslationFormset class
    :rtype: type
    """
    num_languages = Language.objects.count()
    return inlineformset_factory(
        parent_model=POICategory,
        model=POICategoryTranslation,
        form=POICategoryTranslationForm,
        formset=BaseInlinePOICategoryTranslationFormSet,
        min_num=num_languages,
        max_num=num_languages,
    )
