"""
This module contains the API client to interact with the SUMM.AI API
"""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING

import aiohttp
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from ..cms.utils.stringify_list import iter_to_string
from ..core.utils.machine_translation_api_client import MachineTranslationApiClient
from ..core.utils.machine_translation_provider import MachineTranslationProvider
from .utils import (
    HTMLSegment,
    PatientTaskQueue,
    SummAiInvalidJSONError,
    SummAiRateLimitingExceeded,
    SummAiRuntimeError,
    TextField,
    TranslationHelper,
    worker,
)

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from collections.abc import Callable
    from typing import Any, Iterator

    from aiohttp import ClientSession
    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

    from ..cms.models.pages.page import Page

logger = logging.getLogger(__name__)


class SummAiApiClient(MachineTranslationApiClient):
    """
    SUMM.AI API client to get German pages in Easy German language.
    """

    def __init__(self, request: HttpRequest, form_class: ModelFormMetaclass) -> None:
        """
        Constructor initializes the class variables

        :param region: The current region
        :param form_class: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
                           subclass of the current content type
        """
        super().__init__(request, form_class)
        if not MachineTranslationProvider.is_permitted(
            request.region, request.user, form_class._meta.model
        ):
            raise RuntimeError(
                f'Machine translations are disabled for content type "{form_class._meta.model}" and {request.user!r}.'
            )
        if not settings.SUMM_AI_ENABLED:
            raise RuntimeError("SUMM.AI is disabled globally.")
        if not self.region.summ_ai_enabled:
            raise RuntimeError(f"SUMM.AI is disabled in {self.region!r}.")

    async def translate_text_field(
        self, session: ClientSession, text_field: TextField
    ) -> TextField:
        """
        Uses :meth:`aiohttp.ClientSession.post` to perform an asynchronous POST request to the SUMM.AI API.
        After the translation is finished, the processing is delegated to the specific textfield's
        :meth:`~integreat_cms.summ_ai_api.utils.TextField.translate`.

        :param session: The session object which is used for the request
        :param text_field: The text field to be translated
        :return: The modified text field containing the translated text

        Note that :func:`~integreat_cms.summ_ai_api.utils.worker` currently not only counts :class:`~integreat_cms.summ_ai_api.utils.SummAiRateLimitingExceeded`
        but also :class:`~integreat_cms.summ_ai_api.utils.SummAiInvalidJSONError` as a rate limit hit and enqueues the task again.

        :raises SummAiRuntimeError: If text_field is none or text is empty
        :raises SummAiInvalidJSONError: Invalid JSON response returned by the API
        :raises SummAiRateLimitingExceeded: If query runs into rate limit (429 or 529 response)
        """

        logger.debug("Translating %r", text_field)
        # Use test region for development
        user = settings.TEST_REGION_SLUG if settings.DEBUG else self.region.slug
        # Set the language level to "plain" if the region prefers Plain German
        output_language_level = (
            "plain"
            if self.request.region.slug in settings.SUMM_AI_PLAIN_GERMAN_REGIONS
            else "easy"
        )
        if (
            text_field is None
            or (isinstance(text_field, TextField) and not text_field.text)
            or (isinstance(text_field, HTMLSegment) and text_field.segment is None)
        ):
            # This is normally filtered out before this function is called,
            # something must have gone wrong.
            # Raise an exception without immediately catching it!
            raise SummAiRuntimeError("Field to translate is None or empty")
        try:
            async with session.post(
                settings.SUMM_AI_API_URL,
                headers={"Authorization": f"Bearer {settings.SUMM_AI_API_KEY}"},
                json={
                    "input_text": text_field.text,
                    "user": user,
                    "separator": settings.SUMM_AI_SEPARATOR,
                    "is_test": settings.SUMM_AI_TEST_MODE,
                    "is_initial": settings.SUMM_AI_IS_INITIAL,
                    "output_language_level": output_language_level,
                },
            ) as response:
                # Wait for the response
                try:
                    response_data = await response.json()
                except aiohttp.ContentTypeError as e:
                    logger.error(
                        "SUMM.AI API %s response failed to parse as JSON: %s: %s",
                        response.status,
                        type(e),
                        e,
                    )
                    raise SummAiInvalidJSONError(
                        f"API delivered invalid JSON: {response.status} - {await response.text()}"
                    ) from e
                if self.validate_response(response_data, response.status):
                    # Let the field handle the translated text
                    text_field.translate(response_data["translated_text"])
                    # If text is not in response, validate_response()
                    # will raise exceptions - so we don't need an else branch.
        except (aiohttp.ClientError, asyncio.TimeoutError, SummAiRuntimeError) as e:
            logger.error(
                "SUMM.AI translation of %r failed because of %s: %s",
                text_field,
                type(e),
                e,
            )
            text_field.exception = e
        return text_field

    async def translate_text_fields(
        self, loop: AbstractEventLoop, text_fields: Iterator[TextField]
    ) -> chain[list[TextField]]:
        """
        Translate a list of text fields from German into Easy German.
        Create an async task
        :meth:`~integreat_cms.summ_ai_api.summ_ai_api_client.SummAiApiClient.translate_text_field`
        for each entry.

        :param loop: The asyncio event loop
        :param text_fields: The text fields to be translated
        :returns: The list of completed text fields
        """

        # Set a custom SUMM.AI timeout
        timeout = aiohttp.ClientTimeout(total=60 * settings.SUMM_AI_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Create tasks for each text field
            tasks = [
                # translate_text_field() gives us a coroutine that can be executed
                # asynchronously as a task. If we have to repeat the task
                # (e.g. if we run into rate limiting and have to resend the request),
                # we need a NEW coroutine object.
                # For that case, we need a representation of our function which can be
                # evaluated when needed, giving a new coroutine for the task each time.
                partial(self.translate_text_field, session, text_field)
                for text_field in text_fields
            ]

            # If the translation is aborted, set the exception field
            # to both signal that this wasn't translated and to display a reason why
            def abort_function(task: partial, reason: Any) -> None:
                # Retrieve field from arguments to translate_text_field()
                field = task.args[1]
                # Set the exception
                field.exception = f"Machine translation aborted: {reason}"

            # A "patient" task queue which only hands out sleep tasks after a task was reported as failed
            task_generator = PatientTaskQueue(tasks, abort_function=abort_function)

            # Wait for all tasks to finish and collect the results
            worker_results = await asyncio.gather(
                *[
                    worker(loop, task_generator, str(i))
                    for i in range(settings.SUMM_AI_MAX_CONCURRENT_REQUESTS)
                ]
            )
            # Put all results in one single list
            all_results = chain(worker_results)
            return all_results

    def translate_queryset(self, queryset: list[Page], language_slug: str) -> None:
        """
        Translate a queryset of content objects from German into Easy German.
        To increase the speed of the translations, all operations are parallelized.

        :param queryset: The queryset which should be translated
        :param language_slug: The target language slug to translate into
        """

        # Make sure both languages exist
        self.request.region.get_language_or_404(settings.SUMM_AI_GERMAN_LANGUAGE_SLUG)
        easy_german = self.request.region.get_language_or_404(
            settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG
        )

        # Initialize translation helpers for each object instance
        translation_helpers = [
            TranslationHelper(self.request, self.form_class, object_instance)
            for object_instance in queryset
        ]

        # Aggregate all strings that need to be translated
        text_fields = chain(
            *[
                translation_helper.get_text_fields()
                for translation_helper in translation_helpers
            ]
        )

        # Initialize async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Translate queryset asynchronously in parallel
        loop.run_until_complete(self.translate_text_fields(loop, text_fields))

        # Commit changes to the database
        successes = []
        errors = []
        for translation_helper in translation_helpers:
            if TYPE_CHECKING:
                assert translation_helper.german_translation

            if translation_helper.commit(easy_german):
                successes.append(translation_helper.german_translation.title)
            else:
                errors.append(translation_helper.german_translation.title)

        if translation_helpers:
            meta = type(translation_helpers[0].object_instance)._meta
            model_name = meta.verbose_name.title()
            model_name_plural = meta.verbose_name_plural
        else:
            model_name = model_name_plural = ""

        if successes:
            messages.success(
                self.request,
                ngettext_lazy(
                    "{model_name} {object_names} has been successfully translated into Easy German.",
                    "The following {model_name_plural} have been successfully translated into Easy German: {object_names}",
                    len(successes),
                ).format(
                    model_name=model_name,
                    model_name_plural=model_name_plural,
                    object_names=iter_to_string(successes),
                ),
            )

        if errors:
            messages.error(
                self.request,
                ngettext_lazy(
                    "{model_name} {object_names} could not be automatically translated into Easy German.",
                    "The following {model_name_plural} could not be automatically translated into Easy German: {object_names}",
                    len(errors),
                ).format(
                    model_name=model_name,
                    model_name_plural=model_name_plural,
                    object_names=iter_to_string(errors),
                ),
            )

    @classmethod
    def validate_response(cls, response_data: dict, response_status: int) -> bool:
        """
        Checks if translated text is found in SummAiApi-response

        :param response_data: The response-data from SummAiApi
        :param response_status: The response-status form SummAiApi-Request
        :returns: True or False

        :raises SummAiRuntimeError: The response doesn't contain the field translated_text.
        """
        cls.check_internal_server_error(response_status)
        cls.check_rate_limit_exceeded(response_status)

        if "translated_text" not in response_data:
            if "error" in response_data:
                raise SummAiRuntimeError(
                    f"API error: {response_status} - {response_data['error']}"
                )
            raise SummAiRuntimeError(
                f"Unexpected API result: {response_status} - {response_data!r}"
            )
        return True

    @staticmethod
    def check_internal_server_error(response_status: int) -> bool:
        """
        Checks if we got a HTTP 500 error

        :param response_status: The response-status form SummAiApi-Request

        :returns: False (if the response_status is not 500)

        :raises SummAiRuntimeError: If the response_status is 500
        """
        if response_status == 500:
            logger.error("SUMM.AI API has internal server error")
            raise SummAiRuntimeError("API has internal server error")
        return False

    @staticmethod
    def check_rate_limit_exceeded(response_status: int) -> bool:
        """
        Checks if the limit of requests was exceeded (triggered by response_status=429 or 529) and logs this occurrence

        :param response_status: The response-status form SummAiApi-Request
        :returns: False (if the response_status is neither 429 nor 529)

        :raises SummAiRateLimitingExceeded: If the response_status is 429 or 529
        """
        if response_status in (429, 529):
            logger.error(
                "SUMM.AI translation is waiting for %ss because the rate limit has been exceeded",
                settings.SUMM_AI_RATE_LIMIT_COOLDOWN,
            )
            raise SummAiRateLimitingExceeded
        return False
