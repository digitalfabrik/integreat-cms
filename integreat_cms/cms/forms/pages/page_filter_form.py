import logging

from django import forms
from django.utils.translation import ugettext_lazy as _

from ..custom_filter_form import CustomFilterForm
from ...constants import translation_status

logger = logging.getLogger(__name__)


class PageFilterForm(CustomFilterForm):
    """
    Form for filtering page objects
    """

    translation_status = forms.MultipleChoiceField(
        label=_("Translation status"),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "default-checked"}),
        choices=translation_status.CHOICES,
        initial=[key for (key, val) in translation_status.CHOICES],
        required=False,
    )
    query = forms.CharField(required=False)

    def __init__(self, **kwargs):
        r"""
        Initialize page filter form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        # Instantiate Form
        super().__init__(**kwargs)
        logger.debug("PageFilterForm initialized with data %r", self.data)

    def apply(self, pages, language_slug):
        """
        Filter the pages list according to the given filter data

        :param pages: The list of pages
        :type pages: list

        :param language_slug: The slug of the current language
        :type language_slug: str

        :return: The filtered page list
        :rtype: list
        """
        if self.is_enabled:
            logger.debug("Page tree filtered with changed data %r", self.changed_data)
            if "query" in self.changed_data:
                pages = self.filter_by_query(pages, language_slug)
            if "translation_status" in self.changed_data:
                pages = self.filter_by_translation_status(pages, language_slug)
        return pages

    def filter_by_query(self, pages, language_slug):
        """
        Filter the pages list by a given search query

        :param pages: The list of pages
        :type pages: list

        :param language_slug: The slug of the current language
        :type language_slug: str

        :return: The filtered page list
        :rtype: list
        """
        query = self.cleaned_data["query"].lower()
        # Buffer variable because the pages list should not be modified during iteration
        filtered_pages = []
        for page in pages:
            translation = page.get_translation(language_slug)
            if translation and (
                query in translation.slug or query in translation.title.lower()
            ):
                filtered_pages.append(page)
        return filtered_pages

    def filter_by_translation_status(self, pages, language_slug):
        """
        Filter the pages list by a given translation status

        :param pages: The list of pages
        :type pages: list

        :param language_slug: The slug of the current language
        :type language_slug: str

        :return: The filtered page list
        :rtype: list
        """
        selected_status = self.cleaned_data["translation_status"]
        # Buffer variable because the pages list should not be modified during iteration
        filtered_pages = []
        for page in pages:
            _, translation_state = page.translation_states.get(language_slug)
            if translation_state in selected_status:
                filtered_pages.append(page)
        return filtered_pages
