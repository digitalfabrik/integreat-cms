from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Mapping
from datetime import date, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import aiohttp
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from ..cms.constants import language_color, matomo_periods
from .utils import async_get_translation_slug

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from collections.abc import KeysView
    from typing import Any, TypeGuard

    from aiohttp import ClientSession
    from django.utils.functional import Promise

    from ..cms.models import Language, Page, Region

logger = logging.getLogger(__name__)


class MatomoException(Exception):
    """
    Custom Exception class for errors during interaction with Matomo
    """


class MatomoApiClient:
    """
    This class helps to interact with Matomo API.
    There are three functions which can be used publicly:

    * :func:`~integreat_cms.matomo_api.matomo_api_client.MatomoApiClient.get_matomo_id`: Retrieve the Matomo ID belonging to the given Matomo access token
    * :func:`~integreat_cms.matomo_api.matomo_api_client.MatomoApiClient.get_total_visits`: Retrieve the total visits for the current region
    * :func:`~integreat_cms.matomo_api.matomo_api_client.MatomoApiClient.get_visits_per_language`: Retrieve the visits for the current region by language
    """

    #: Matomo API-key
    matomo_token: str | None = None
    #: Matomo ID
    matomo_id: int | None = None
    #: The active languages
    languages: list[Language] = []

    def __init__(self, region: Region) -> None:
        """
        Constructor initializes the class variables

        :param region: The region this Matomo API Manager connects to
        """
        self.region_slug = region.slug
        self.region_name = region.name
        self.matomo_token = region.matomo_token
        self.matomo_id = region.matomo_id
        self.languages = region.active_languages

    async def fetch(
        self,
        session: ClientSession,
        **kwargs: Any,
    ) -> dict[str, Any] | list[int]:
        r"""
        Uses :meth:`aiohttp.ClientSession.get` to perform an asynchronous GET request to the Matomo API.

        :param session: The session object which is used for the request
        :param \**kwargs: The parameters which are passed to the Matomo API
        :raises ~integreat_cms.matomo_api.matomo_api_client.MatomoException: When a :class:`~aiohttp.ClientError` was raised during a
                                                               Matomo API request

        :return: The parsed :mod:`json` result
        """
        # The default get parameters for all requests
        query_params = {
            "format": "JSON",
            "module": "API",
            "token_auth": self.matomo_token,
        }
        # Update with the custom params for this request
        query_params.update(kwargs)

        def mask_token_auth(req_url: str) -> str:
            return re.sub("&token_auth=[^&]+", "&token_auth=********", req_url)

        url = f"{settings.MATOMO_URL}/?{urlencode(query_params)}"
        logger.debug(
            "Requesting %r: %s",
            query_params.get("method"),
            # Mask auth token in log
            mask_token_auth(url),
        )
        try:
            async with session.get(url) as response:
                response_data = await response.json()
                if (
                    isinstance(response_data, dict)
                    and response_data.get("result") == "error"
                ):
                    raise MatomoException(response_data["message"])
                return response_data
        except aiohttp.ClientError as e:
            raise MatomoException(
                f"An error occurred {mask_token_auth(str(e))}",
            ) from None

    async def get_matomo_id_async(self, **query_params: Any) -> list[int]:
        r"""
        Async wrapper to fetch the Matomo ID with :mod:`aiohttp`.
        Opens a :class:`~aiohttp.ClientSession` and calls :func:`~integreat_cms.matomo_api.matomo_api_client.MatomoApiClient.fetch`.
        Called from :func:`~integreat_cms.matomo_api.matomo_api_client.MatomoApiClient.get_matomo_id`.

        :param \**query_params: The parameters which are passed to the Matomo API
        :return: The parsed :mod:`json` result
        :raises ~integreat_cms.matomo_api.matomo_api_client.MatomoException: When a :class:`~aiohttp.ClientError` was raised during a
                                                                             Matomo API request
        """
        async with aiohttp.ClientSession() as session:
            result = await self.fetch(session, **query_params)
            if TYPE_CHECKING:
                assert isinstance(result, list)
            return result

    def get_matomo_id(self, token_auth: str) -> int:
        """
        Returns the matomo website id based on the provided authentication key.

        :param token_auth: The Matomo authentication token which should be used
        :raises ~integreat_cms.matomo_api.matomo_api_client.MatomoException: When a :class:`~aiohttp.ClientError` was raised during a
                                                               Matomo API request or the access token is not correct

        :return: ID of the connected Matomo instance
        """
        # Initialize async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Execute async request to Matomo API
        response = loop.run_until_complete(
            self.get_matomo_id_async(
                token_auth=token_auth,
                method="SitesManager.getSitesIdWithAtLeastViewAccess",
            ),
        )

        try:
            return response[0]
        except IndexError as e:
            # If no id is returned, there is no user with the given access token
            raise MatomoException(
                f"The access token for {self.region_name} is not correct.",
            ) from e

    async def get_total_visits_async(
        self,
        query_params: dict[str, str | int | None],
    ) -> dict[str, Any]:
        """
        Async wrapper to fetch the total visits with :mod:`aiohttp`.
        Opens a :class:`~aiohttp.ClientSession` and calls :func:`~integreat_cms.matomo_api.matomo_api_client.MatomoApiClient.fetch`.
        Called from :func:`~integreat_cms.matomo_api.matomo_api_client.MatomoApiClient.get_total_visits`.

        :param query_params: The parameters which are passed to the Matomo API
        :raises ~integreat_cms.matomo_api.matomo_api_client.MatomoException: When a :class:`~aiohttp.ClientError` was raised during a
                                                               Matomo API request

        :return: The parsed :mod:`json` result
        """
        async with aiohttp.ClientSession() as session:
            result = await self.fetch(
                session,
                **query_params,
            )
            if TYPE_CHECKING:
                assert isinstance(result, dict)
            return result

    def get_total_visits(
        self,
        start_date: date,
        end_date: date,
        period: str = matomo_periods.DAY,
    ) -> dict[str, Any]:
        """
        Returns the total calls within a time range for all languages.

        :param start_date: Start date
        :param end_date: End date
        :param period: The period (one of :attr:`~integreat_cms.cms.constants.matomo_periods.CHOICES` -
                       defaults to :attr:`~integreat_cms.cms.constants.matomo_periods.DAY`)
        :raises ~integreat_cms.matomo_api.matomo_api_client.MatomoException: When a :class:`~aiohttp.ClientError` was raised during a
                                                               Matomo API request

        :return: The total visits in the ChartData format expected by ChartJs
        """
        query_params = {
            "date": f"{start_date},{end_date}",
            "idSite": self.matomo_id,
            "method": "VisitsSummary.getActions",
            "period": period,
        }

        # Initialize async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Execute async request to Matomo API
        dataset = loop.run_until_complete(self.get_total_visits_async(query_params))

        return {
            # Send original labels for usage in the CSV export (convert to list because type dict_keys is not JSON-serializable)
            "exportLabels": list(dataset.keys()),
            # Return the data in the ChartData format expected by ChartJs
            "chartData": {
                # Make labels more readable
                "labels": self.simplify_date_labels(dataset.keys(), period),
                "datasets": [
                    {
                        "label": _("Total Accesses"),
                        "backgroundColor": language_color.TOTAL_ACCESS,
                        "borderColor": language_color.TOTAL_ACCESS,
                        "data": list(dataset.values()),
                    },
                ],
            },
        }

    async def get_visits_per_language_async(
        self,
        loop: AbstractEventLoop,
        query_params: dict[str, Any],
        languages: list[Language],
    ) -> list[dict[str, Any]]:
        """
        Async wrapper to fetch the total visits with :mod:`aiohttp`.
        Opens a :class:`~aiohttp.ClientSession`, creates a :class:`~asyncio.Task` for each language to call
        :func:`~integreat_cms.matomo_api.matomo_api_client.MatomoApiClient.fetch` and waits for all tasks to finish with
        :func:`~asyncio.gather`.
        The returned list of gathered results has the correct order in which the tasks were created (at first the
        ordered list of languages and the last element is the task for the total visits).
        Called from :func:`~integreat_cms.matomo_api.matomo_api_client.MatomoApiClient.get_visits_per_language`.

        :param loop: The asyncio event loop
        :param query_params: The parameters which are passed to the Matomo API
        :param languages: The list of languages which should be retrieved
        :raises ~integreat_cms.matomo_api.matomo_api_client.MatomoException: When a :class:`~aiohttp.ClientError` was raised during a
                                                               Matomo API request

        :return: The list of gathered results
        """
        async with aiohttp.ClientSession() as session:
            # Create tasks for visits by language
            tasks = [
                loop.create_task(
                    self.fetch(
                        session,
                        **query_params,
                        segment=f"pageUrl=@/{language.slug}/wp-json/extensions/v3/,pageUrl=@/api/v3/{self.region_slug}/{language.slug}/",
                    ),
                )
                for language in languages
            ]
            # Create separate task to gather offline download hits
            tasks.append(
                loop.create_task(
                    self.fetch(
                        session,
                        **query_params,
                        segment="pageUrl=@/wp-json/extensions/v3/pages,pageUrl=$/pages/",
                    ),
                ),
            )
            # Create separate task to gather WebApp download hits
            tasks.append(
                loop.create_task(
                    self.fetch(
                        session,
                        **query_params,
                        segment="pageUrl=@/children/?depth",
                    ),
                ),
            )
            # Create task for all downloads
            tasks.append(
                loop.create_task(
                    self.fetch(
                        session,
                        **query_params,
                    ),
                ),
            )
            # Wait for all tasks to finish and collect the results
            # (the results are sorted in the order the tasks were created)
            result = await asyncio.gather(*tasks)
            # We're not retrieving the matomo id as part of the tasks, thus we know that the result is a list of dicts, not a list of list of ints.
            if TYPE_CHECKING:

                def is_dict_list(
                    lst: list[dict[str, Any] | list[int]],
                ) -> TypeGuard[list[dict[str, Any]]]:
                    return all(isinstance(d, dict) for d in lst)

                assert is_dict_list(result)
            return result

    def get_visits_per_language(
        self,
        start_date: date,
        end_date: date,
        period: str,
    ) -> dict[str, Any]:
        """
        Returns the total unique visitors in a timerange as defined in period

        :param start_date: Start date
        :param end_date: End date
        :param period: The period (one of :attr:`~integreat_cms.cms.constants.matomo_periods.CHOICES`)
        :return: The visits per language in the ChartData format expected by ChartJs
        :raises ~integreat_cms.matomo_api.matomo_api_client.MatomoException: When a :class:`~aiohttp.ClientError` was raised during a
                                                                             Matomo API request
        """
        query_params = {
            "date": f"{start_date},{end_date}",
            "expanded": "1",
            "filter_limit": "-1",
            "format_metrics": "1",
            "idSite": self.matomo_id,
            "method": "VisitsSummary.getActions",
            "period": period,
        }
        logger.debug(
            "Query params: %r",
            query_params,
        )
        # Convert languages to a list to force an evaluation in the sync function
        # (in Django, database queries cannot be executed in async functions without more ado)
        languages = list(self.languages)

        # Initialize async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Execute async request to Matomo API
        logger.debug("Fetching visits for languages %r asynchronously.", languages)
        datasets = loop.run_until_complete(
            self.get_visits_per_language_async(loop, query_params, languages),
        )
        logger.debug("All asynchronous fetching tasks have finished.")
        # The last dataset contains the total visits
        total_visits = datasets.pop()
        # Get the separately created datasets for webapp downloads
        webapp_downloads = datasets.pop()
        # Get the separately created datasets for offline downloads
        offline_downloads = datasets.pop()

        language_data, language_legends = self.get_language_data(languages, datasets)
        access_data, access_legends = self.get_access_data(
            total_visits,
            webapp_downloads,
            offline_downloads,
        )

        return {
            # Send original labels for usage in the CSV export (convert to list because type dict_keys is not JSON-serializable)
            "exportLabels": list(total_visits.keys()),
            # Return the data in the ChartData format expected by ChartJs
            "chartData": {
                # Make labels more readable
                "labels": self.simplify_date_labels(total_visits.keys(), period),
                "datasets": language_data + access_data,
            },
            "legend": render_to_string(
                "statistics/_statistics_legend.html",
                {"languages": language_legends, "accesses": access_legends},
            ),
        }

    @staticmethod
    def simplify_date_labels(date_labels: KeysView[str], period: str) -> list[Promise]:
        """
        Convert the dates returned by Matomo to more readable labels

        :param date_labels: The date labels returned by Matomo
        :param period: The period of the labels (determines the format)
        :return: The readable labels
        """
        simplified_date_labels = []
        if period == matomo_periods.DAY:
            # Convert string labels to date objects (the format for daily period is the iso format YYYY-MM-DD)
            date_objects = [
                date.fromisoformat(date_label) for date_label in date_labels
            ]
            # Convert date objects to more readable labels
            if date.today().year == date_objects[0].year:
                # If the first label is in the current year, omit the year for all dates
                simplified_date_labels = [
                    date_obj.strftime("%d.%m.") for date_obj in date_objects
                ]
            else:
                # Else, include the year
                simplified_date_labels = [
                    date_obj.strftime("%d.%m.%Y") for date_obj in date_objects
                ]
        elif period == matomo_periods.WEEK:
            # Convert string labels to date objects (the format for weekly period is YYYY-MM-DD,YYYY-MM-DD)
            date_objects = [
                datetime.strptime(date_label.split(",")[0], "%Y-%m-%d").date()
                for date_label in date_labels
            ]
            # Convert date objects to more readable labels
            if date.today().year == date_objects[0].year:
                # If the first label is in the current year, omit the year for all dates
                simplified_date_labels = [
                    _("CW") + date_obj.strftime(" %W") for date_obj in date_objects
                ]
            else:
                # Else, include the year
                simplified_date_labels = [
                    date_obj.strftime("%Y ") + _("CW") + date_obj.strftime(" %W")
                    for date_obj in date_objects
                ]
        elif period == matomo_periods.MONTH:
            # Convert string labels to date objects (the format for monthly period is YYYY-MM)
            date_objects = [
                datetime.strptime(date_label, "%Y-%m").date()
                for date_label in date_labels
            ]
            # Convert date objects to more readable labels
            if date.today().year == date_objects[0].year:
                # If the first label is in the current year, omit the year for all dates
                simplified_date_labels = [
                    _(date_obj.strftime("%B")) for date_obj in date_objects
                ]
            else:
                # Else, include the year
                simplified_date_labels = [
                    _(date_obj.strftime("%B")) + date_obj.strftime(" %Y")
                    for date_obj in date_objects
                ]
        else:
            # This means the period is "year" (convert to list because type dict_keys is not JSON-serializable)
            simplified_date_labels = list(date_labels)
        return simplified_date_labels

    @staticmethod
    def get_language_data(
        languages: list[Language],
        datasets: list[dict],
    ) -> tuple[list[dict], list[str]]:
        """
        Structure the datasets for languages in a chart.js-compatible format,
        returning it and the custom legend entries

        :param languages: The list of languages
        :param datasets: The Matomo datasets
        :return: The chart.js-datasets and custom legend entries
        """
        data_entries = []
        legend_entries = []

        for language, dataset in zip(languages, datasets, strict=False):
            data_entries.append(
                {
                    "label": language.translated_name,
                    "backgroundColor": language.language_color,
                    "borderColor": language.language_color,
                    "data": list(dataset.values()),
                },
            )
            legend_entries.append(
                render_to_string(
                    "statistics/_statistics_legend_item.html",
                    {
                        "name": language.translated_name,
                        "color": language.language_color,
                        "language": language,
                    },
                ),
            )
        return data_entries, legend_entries

    @staticmethod
    def get_access_data(
        total_visits: dict,
        webapp_downloads: dict,
        offline_downloads: dict,
    ) -> tuple[list[dict], list[str]]:
        """
        Structure the datasets for accesses in a chart.js-compatible format,
        returning it and the custom legend entries

        :param total_visits: The total amount of visits
        :param webapp_downloads: The amount of visits via the WebApp
        :param offline_downloads: The amount of offline downloads
        :return: The chart.js-datasets and custom legend entries
        """
        data_entries = [
            {
                "label": _("Phone App Accesses"),
                "backgroundColor": language_color.OFFLINE_ACCESS,
                "borderColor": language_color.OFFLINE_ACCESS,
                "data": list(offline_downloads.values()),
            },
            {
                "label": _("WebApp Accesses"),
                "backgroundColor": language_color.WEB_APP_ACCESS,
                "borderColor": language_color.WEB_APP_ACCESS,
                "data": list(webapp_downloads.values()),
            },
            {
                "label": _("Total Accesses"),
                "backgroundColor": language_color.TOTAL_ACCESS,
                "borderColor": language_color.TOTAL_ACCESS,
                "data": list(total_visits.values()),
            },
        ]

        legend_entries = [
            render_to_string(
                "statistics/_statistics_legend_item.html",
                {
                    "name": _("Phone App Accesses"),
                    "color": language_color.OFFLINE_ACCESS,
                },
            ),
            render_to_string(
                "statistics/_statistics_legend_item.html",
                {
                    "name": _("WebApp Accesses"),
                    "color": language_color.WEB_APP_ACCESS,
                },
            ),
            render_to_string(
                "statistics/_statistics_legend_item.html",
                {
                    "name": _("Total Accesses"),
                    "color": language_color.TOTAL_ACCESS,
                },
            ),
        ]
        return data_entries, legend_entries

    async def get_page_accesses_async(
        self,
        loop: AbstractEventLoop,
        query_params: dict[str, Any],
        languages: list[Language],
        pages: list[Page],
    ) -> list[dict[str, Any]]:
        """
        :param loop: The asyncio event loop
        :param query_params: The parameters which are passed to the Matomo API
        :param languages: The list of languages which should be retrieved
        :param pages: The list of pages which should be retrieved
        :raises ~integreat_cms.matomo_api.matomo_api_client.MatomoException: When a :class:`~aiohttp.ClientError` was raised during a
                                                               Matomo API request
        :return:
        """
        translation_slugs = await async_get_translation_slug(pages, languages)
        async with aiohttp.ClientSession() as session:
            # Create tasks for visits by language
            tasks = [
                loop.create_task(
                    self.retrieve_accesses_for_page(
                        session,
                        query_params,
                        page_id=page_id,
                        lang_slug=lang_slug,
                        full_slug=full_slug,
                    )
                )
                for page_id, langs in translation_slugs.items()
                for lang_slug, full_slug in langs.items()
            ]
            # Wait for all tasks to finish and collect the results
            # (the results are sorted in the order the tasks were created)
            return await asyncio.gather(*tasks)

    async def retrieve_accesses_for_page(
        self,
        session: aiohttp.ClientSession,
        query_params: dict[str, Any],
        page_id: int,
        lang_slug: str,
        full_slug: str,
    ) -> dict:
        """
        This function retrieves the accesses for a single page (from Matomo).

        :param session: The current session
        :param query_params: The parameters which are passed to the Matomo API
        :param page_id: Id of page for which accesses are retrieved
        :param lang_slug: Language slug for which accesses are retrieved
        :param full_slug: The absolute url slug for the page
        :return: dict of page and it's accesses
        """
        return {
            page_id: {
                lang_slug: await self.fetch(
                    session,
                    **query_params,
                    segment=f"pageUrl=@/children/?depth=2&url={full_slug}",
                )
            }
        }

    def get_page_accesses(
        self, start_date: date, end_date: date, period: str, region: Region
    ) -> dict[int, dict[str, int]]:
        """
        This function handles the page based accesses

        :param start_date: Start date
        :param end_date: End date
        :param period: The period (one of :attr:`~integreat_cms.cms.constants.matomo_periods.CHOICES`)
        :param region: The region for which we want our page based accesses
        :return: The page accesses for the given region
        :raises ~integreat_cms.matomo_api.matomo_api_client.MatomoException: When a :class:`~aiohttp.ClientError` was raised during a
                                                                         Matomo API request
        """
        query_params = {
            "date": f"{start_date},{end_date}",
            "expanded": "1",
            "filter_limit": "-1",
            "format_metrics": "1",
            "idSite": self.matomo_id,
            "method": "VisitsSummary.getActions",
            "period": period,
        }
        languages = list(self.languages)
        pages = region.get_pages()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.debug("Fetching visits for languages %r asynchronously.", languages)
        datasets = loop.run_until_complete(
            self.get_page_accesses_async(loop, query_params, languages, pages)
        )

        def deep_merge(*dicts: Mapping[Any, Any]) -> dict:
            """
            Recursively merges dictionaries. Values in later dictionaries override earlier ones
            for non-dict values, while dictionaries are merged recursively.
            """
            merged: dict[Any, Any] = {}
            for d in dicts:
                for key, value in d.items():
                    if (
                        key in merged
                        and isinstance(merged[key], Mapping)
                        and isinstance(value, Mapping)
                    ):
                        # Recursively merge dictionaries
                        merged[key] = deep_merge(merged[key], value)
                    else:
                        # Otherwise, override or add the value
                        merged[key] = value
            return merged

        return deep_merge(*datasets)
