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
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from ..cms.utils.stringify_list import iter_to_string
from ..core.utils.machine_translation_api_client import MachineTranslationApiClient
from ..core.utils.machine_translation_provider import MachineTranslationProvider
from .utils import (
    BudgetEstimate,
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

    from ..cms.models.abstract_content_translation import AbstractContentTranslation
    from ..cms.models.pages.page import Page
    from ..cms.models.regions.region import Region

from ..core.utils.word_count import word_count

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

    def check_usage(
        self,
        region: Region,
        source_translation: str | AbstractContentTranslation,
        allocated_budget: int = 0,
    ) -> tuple[bool, int]:
        """
        This function checks if the attempted translation would exceed the region's word limit

        :param region: region for which to check usage
        :param source_translation: single content object
        :param allocated_budget: how many additional words should be considered already spent
        :return: translation would exceed limit, word count of attempted translation
        """
        words = word_count(source_translation)

        region.refresh_from_db()
        # Allow up to SUMM_AI_SOFT_MARGIN more words than the actual limit
        word_count_leeway = max(
            1, words + allocated_budget - settings.SUMM_AI_SOFT_MARGIN
        )
        translation_exceeds_limit = region.summ_ai_budget_remaining < word_count_leeway

        return (translation_exceeds_limit, words)

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
        except (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            SummAiRuntimeError,
        ) as e:
            logger.error(
                "SUMM.AI translation of %r failed because of %s: %s",
                text_field,
                type(e),
                e,
            )
            text_field.exception = e
        return text_field

    async def translate_text_fields(
        self, loop: AbstractEventLoop, translation_helpers: list[TranslationHelper]
    ) -> chain[list[TextField]]:
        """
        Translate a list of text fields from German into Easy German.
        Create an async task
        :meth:`~integreat_cms.summ_ai_api.summ_ai_api_client.SummAiApiClient.translate_text_field`
        for each entry.

        :param loop: The asyncio event loop
        :param translation_helpers: The translation helper to be translated
        :returns: The list of completed text fields
        """

        # Set a custom SUMM.AI timeout
        timeout = aiohttp.ClientTimeout(total=60 * settings.SUMM_AI_TIMEOUT)
        translations = iter(translation_helpers)
        async with aiohttp.ClientSession(timeout=timeout) as session:

            # If the translation is aborted, set the exception field
            # to both signal that this wasn't translated and to display a reason why
            def abort_function(task: partial, reason: Any) -> None:
                # Retrieve field from arguments to translate_text_field()
                field = task.args[1]
                # Set the exception
                field.exception = f"Machine translation aborted: {reason}"

            # A "patient" task queue which only hands out sleep tasks after a task was reported as failed
            task_generator: PatientTaskQueue[partial] = PatientTaskQueue(
                [], abort_function=abort_function
            )

            async def manage() -> None:
                """
                A management task to schedule more translation tasks, but only if the sum of all text fields
                of the whole content translation won't exceed the regions remaining budget.

                The goal is to add all text fields of the next content translation if it fits in the budget,
                as long as there are fewer than ``SUMM_AI_MAX_CONCURRENT_REQUESTS`` tasks in the :class:`~integreat_cms.summ_ai_api.utils.PatientTaskQueue`
                – but at least one content translation worth of text fields per run (unless there are no more translation objects to try).
                Finally, if successful and we were able to add any tasks, schedule another ``manage()`` to repeat this once the workers processed all the items.

                This tries to always keep the queue filled with at least as many tasks as there are workers,
                such that there is no situation that a worker attempts to fetch
                """
                # Telling the task_generator to stall workers asking for new tasks until we're done adding them
                task_generator.more_tasks_pending += 1
                while translation_helper := next(translations, None):
                    # allocate_budget has to run in a sync context for django/db reasons, hence why it looks this ugly.
                    # thread_sensitive does not technically need to be changed to False,
                    # but the way we test this django app would give us a
                    #   RuntimeError: You cannot submit onto CurrentThreadExecutor from its own thread
                    # otherwise.
                    if not await sync_to_async(
                        translation_helper.allocate_budget, thread_sensitive=False
                    )():
                        # This content translation object does not fit in the budget, but maybe the next will be smaller?
                        continue

                    # Create tasks for each text field
                    task_generator.extend(
                        [
                            # translate_text_field() gives us a coroutine that can be executed
                            # asynchronously as a task. If we have to repeat the task
                            # (e.g. if we run into rate limiting and have to resend the request),
                            # we need a NEW coroutine object.
                            # For that case, we need a representation of our function which can be
                            # evaluated when needed, giving a new coroutine for the task each time.
                            partial(self.translate_text_field, session, text_field)
                            for text_field in translation_helper.get_text_fields()
                        ]
                    )

                    # We're adding 1 because the next manage will also be a task
                    if (
                        len(task_generator) + 1
                        >= settings.SUMM_AI_MAX_CONCURRENT_REQUESTS
                    ):
                        task_generator.append(partial(manage))
                        break

                # Telling the task_generator we're done adding new tasks and
                task_generator.more_tasks_pending -= 1

            # We want to fill the queue before the worker can get to work.
            # This is critical because if the queue starts out with only the first manage task,
            # then while the first worker is busy creating the next tasks, the other workers
            # might already find an empty queue and quit, leaving only the first worker to all tasks.
            await manage()

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
        region = self.request.region

        # Make sure both languages exist
        region.get_language_or_404(settings.SUMM_AI_GERMAN_LANGUAGE_SLUG)
        easy_german = region.get_language_or_404(
            settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG
        )

        budget_estimate = BudgetEstimate(
            check_usage=lambda source_translation, allocated_budget: self.check_usage(
                region, source_translation, allocated_budget
            )
        )

        # Initialize translation helpers for each object instance
        translation_helpers = [
            TranslationHelper(
                self.request,
                self.form_class,
                object_instance,
                budget_estimate=budget_estimate,
            )
            for object_instance in queryset
        ]

        # Initialize async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Translate queryset asynchronously in parallel
        loop.run_until_complete(self.translate_text_fields(loop, translation_helpers))

        # Refresh the region object in case the budget used changed in the meantime
        region.refresh_from_db()

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

            region.summ_ai_budget_used += translation_helper.word_count
            region.save()

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
