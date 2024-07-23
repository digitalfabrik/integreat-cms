from __future__ import annotations

import asyncio
import logging
import re
from datetime import date, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import aiohttp
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ..cms.constants import language_color, matomo_periods

if TYPE_CHECKING:
    import sys
    from asyncio import AbstractEventLoop
    from collections.abc import KeysView
    from typing import Any, TypeGuard

    from aiohttp import ClientSession
    from django.utils.functional import Promise

    from ..cms.models import Language, Region

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
        self, session: ClientSession, **kwargs: Any
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

        url = f"{settings.MATOMO_URL}/?{urlencode(query_params)}"
        logger.debug(
            "Requesting %r: %s",
            query_params.get("method"),
            # Mask auth token in log
            re.sub(r"&token_auth=[^&]+", "&token_auth=********", url),
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
            raise MatomoException(str(e)) from e

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
            )
        )

        try:
            return response[0]
        except IndexError as e:
            # If no id is returned, there is no user with the given access token
            raise MatomoException(
                f"The access token for {self.region_name} is not correct."
            ) from e

    async def get_total_visits_async(
        self, query_params: dict[str, str | int | None]
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
        self, start_date: date, end_date: date, period: str = matomo_periods.DAY
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
                    }
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
                    )
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
                )
            )
            # Create separate task to gather WebApp download hits
            tasks.append(
                loop.create_task(
                    self.fetch(
                        session, **query_params, segment="pageUrl=@/children/?depth"
                    ),
                )
            )
            # Create task for all downloads
            tasks.append(
                loop.create_task(
                    self.fetch(
                        session,
                        **query_params,
                    )
                )
            )
            # Wait for all tasks to finish and collect the results
            # (the results are sorted in the order the tasks were created)
            result = await asyncio.gather(*tasks)
            # We're not retrieving the matomo id as part of the tasks, thus we know that the result is a list of dicts, not a list of list of ints.
            if TYPE_CHECKING:

                def is_dict_list(
                    lst: list[dict[str, Any] | list[int]]
                ) -> TypeGuard[list[dict[str, Any]]]:
                    return all(isinstance(d, dict) for d in lst)

                assert is_dict_list(result)
            return result

    def get_visits_per_language(
        self, start_date: date, end_date: date, period: str
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
            self.get_visits_per_language_async(loop, query_params, languages)
        )
        logger.debug("All asynchronous fetching tasks have finished.")
        # The last dataset contains the total visits
        total_visits = datasets.pop()
        # Get the separately created datasets for webapp downloads
        webapp_downloads = datasets.pop()
        # Get the separately created datasets for offline downloads
        offline_downloads = datasets.pop()

        return {
            # Send original labels for usage in the CSV export (convert to list because type dict_keys is not JSON-serializable)
            "exportLabels": list(total_visits.keys()),
            # Return the data in the ChartData format expected by ChartJs
            "chartData": {
                # Make labels more readable
                "labels": self.simplify_date_labels(total_visits.keys(), period),
                "datasets":
                # The datasets for the visits by language
                [
                    {
                        "label": language.translated_name,
                        "backgroundColor": language.language_color,
                        "borderColor": language.language_color,
                        "data": list(dataset.values()),
                    }
                    # zip aggregates two lists into tuples, e.g. zip([1,2,3], [4,5,6])=[(1,4), (2,5), (3,6)]
                    # In this case, it matches the languages to their respective dataset (because the datasets are ordered)
                    for language, dataset in zip(languages, datasets)
                ]
                # The dataset for offline downloads
                + [
                    {
                        "label": _("Offline Accesses"),
                        "backgroundColor": language_color.OFFLINE_ACCESS,
                        "borderColor": language_color.OFFLINE_ACCESS,
                        "data": list(offline_downloads.values()),
                    }
                ]
                # The dataset for online/web app downloads
                + [
                    {
                        "label": _("WebApp Accesses"),
                        "backgroundColor": language_color.WEB_APP_ACCESS,
                        "borderColor": language_color.WEB_APP_ACCESS,
                        "data": list(webapp_downloads.values()),
                    }
                ]
                # The dataset for total visits
                + [
                    {
                        "label": _("Total Accesses"),
                        "backgroundColor": language_color.TOTAL_ACCESS,
                        "borderColor": language_color.TOTAL_ACCESS,
                        "data": list(total_visits.values()),
                    }
                ],
            },
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
