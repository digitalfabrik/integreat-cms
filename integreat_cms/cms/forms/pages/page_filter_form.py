from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Any

    from ...models import Page

from ...constants import status, translation_status
from ..custom_filter_form import CustomFilterForm

logger = logging.getLogger(__name__)


class PageFilterForm(CustomFilterForm):
    """
    Form for filtering page objects
    """

    status = forms.ChoiceField(
        label=_("Publication status"),
        choices=[("", _("All"))] + status.CHOICES,
        required=False,
    )

    date_from = forms.DateField(
        label=_("From"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "default-value", "data-default-value": ""},
        ),
        required=False,
    )

    date_to = forms.DateField(
        label=_("To"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "default-value", "data-default-value": ""},
        ),
        required=False,
    )

    translation_status = forms.MultipleChoiceField(
        label=_("Translation status"),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "default-checked"}),
        choices=translation_status.CHOICES,
        initial=[key for (key, val) in translation_status.CHOICES],
        required=False,
    )

    exclude_pages_without_content = forms.BooleanField(
        label=_("Exclude pages without content"),
        required=False,
    )

    query = forms.CharField(required=False)

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize page filter form

        :param \**kwargs: The supplied keyword arguments
        """
        # Instantiate Form
        super().__init__(**kwargs)
        logger.debug("PageFilterForm initialized with data %r", self.data)

    def apply(self, pages: list[Page], language_slug: str) -> list[Page]:
        """
        Filter the pages list according to the given filter data

        :param pages: The list of pages
        :param language_slug: The slug of the current language
        :return: The filtered page list
        """
        if self.is_enabled:
            logger.debug("Page tree filtered with changed data %r", self.changed_data)
            if "query" in self.changed_data:
                pages = self.filter_by_query(pages, language_slug)
            if "translation_status" in self.changed_data:
                pages = self.filter_by_translation_status(pages, language_slug)
            if "status" in self.changed_data:
                pages = self.filter_by_publication_status(pages, language_slug)
            if "date_from" in self.changed_data:
                pages = self.filter_by_start_date(pages, language_slug)
            if "date_to" in self.changed_data:
                pages = self.filter_by_end_date(pages, language_slug)
            if "exclude_pages_without_content" in self.changed_data:
                pages = self.filter_by_pages_with_content(pages, language_slug)
        return pages

    def filter_by_query(self, pages: list[Page], language_slug: str) -> list[Page]:
        """
        Filter the pages list by a given search query

        :param pages: The list of pages
        :param language_slug: The slug of the current language
        :return: The filtered page list
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

    def filter_by_translation_status(
        self, pages: list[Page], language_slug: str
    ) -> list[Page]:
        """
        Filter the pages list by a given translation status

        :param pages: The list of pages
        :param language_slug: The slug of the current language
        :return: The filtered page list
        """
        selected_status = self.cleaned_data["translation_status"]
        # Buffer variable because the pages list should not be modified during iteration
        filtered_pages = []
        for page in pages:
            _, translation_state = page.translation_states.get(language_slug)
            if translation_state in selected_status:
                filtered_pages.append(page)
        return filtered_pages

    def filter_by_publication_status(
        self, pages: list[Page], language_slug: str
    ) -> list[Page]:
        """
        Filter the pages list by publication status

        :param pages: The list of pages
        :param language_slug: The slug of the current language
        :return: The filtered page list
        """
        selected_status = self.cleaned_data["status"]
        # Buffer variable because the pages list should not be modified during iteration
        filtered_pages = []
        for page in pages:
            translation = page.get_translation(language_slug)
            if translation and translation.status == selected_status:
                filtered_pages.append(page)
        return filtered_pages

    def filter_by_start_date(self, pages: list[Page], language_slug: str) -> list[Page]:
        """
        Filter the pages list by start date

        :param pages: The list of pages
        :param language_slug: The slug of the current language
        :return: The filtered page list
        """
        selected_start_date = self.cleaned_data["date_from"]
        filtered_pages = []
        for page in pages:
            translation = page.get_translation(language_slug)
            if translation and translation.last_updated.date() >= selected_start_date:
                filtered_pages.append(page)
        return filtered_pages

    def filter_by_end_date(self, pages: list[Page], language_slug: str) -> list[Page]:
        """
        Filter the pages list by end date

        :param pages: The list of pages
        :param language_slug: The slug of the current language
        :return: The filtered page list
        """
        selected_end_date = self.cleaned_data["date_to"]
        filtered_pages = []
        for page in pages:
            translation = page.get_translation(language_slug)
            if translation and translation.last_updated.date() <= selected_end_date:
                filtered_pages.append(page)
        return filtered_pages

    def filter_by_pages_with_content(
        self, pages: list[Page], language_slug: str
    ) -> list[Page]:
        """
        Filter only by pages that have content (including empty pages with live content)
        :param pages: The list of pages
        :param language_slug: The slug of the current language
        :return: pages that have content
        """
        filtered_pages = []
        for page in pages:
            translation = page.get_translation(language_slug)
            if translation and (len(translation.content) > 0 or page.mirrored_page):
                filtered_pages.append(page)
        return filtered_pages
