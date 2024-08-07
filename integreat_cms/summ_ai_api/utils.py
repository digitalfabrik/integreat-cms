"""
This module contains helpers for the SUMM.AI API client
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import time
from collections import deque
from html import unescape
from typing import Generic, TYPE_CHECKING, TypeVar

from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from lxml.etree import strip_tags, SubElement
from lxml.html import fromstring, HtmlElement, tostring

if TYPE_CHECKING:
    from collections.abc import Callable
    from functools import partial
    from typing import Any

    from django.forms.models import ModelFormMetaclass
    from django.http import HttpRequest

    from ..cms.models import (
        Language,
        Page,
        PageTranslation,
    )
    from ..cms.models.abstract_content_model import AbstractContentModel
    from ..cms.models.abstract_content_translation import AbstractContentTranslation

from ..cms.constants import status
from ..cms.utils.translation_utils import gettext_many_lazy as __

logger = logging.getLogger(__name__)


class SummAiException(Exception):
    """
    Base class for custom SUMM.AI exceptions
    """


class SummAiRateLimitingExceeded(SummAiException):
    """
    Custom Exception class for running into rate limit in SUMM.AI
    """


class SummAiRuntimeError(SummAiException):
    """
    Custom Exception class for any other errors during interaction with SUMM.AI
    """


class SummAiInvalidJSONError(SummAiException):
    """
    Custom Exception class for faulty responses from SUMM.AI
    """


class TextField:
    """
    A class for simple text fields
    """

    #: The name of the corresponding model field
    name: str
    #: The source text
    text: str
    #: The translated text
    translated_text: str = ""
    #: The exception which occurred during translation, if any
    exception: Exception | None = None

    def __init__(self, name: str, translation: PageTranslation) -> None:
        """
        Constructor initializes the class variables

        :param text: The text to be translated
        """
        self.name = name
        self.text = getattr(translation, name, "").strip()

    def translate(self, translated_text: str) -> None:
        """
        Translate the text of the current text field

        :param translated_text: The translated text
        """
        self.translated_text = translated_text

    def __repr__(self) -> str:
        """
        The representation used for logging

        :return: The canonical string representation of the text field
        """
        return f"<{type(self).__name__} (text: {self.text})>"


# pylint: disable=too-few-public-methods
class HTMLSegment(TextField):
    """
    A class for translatable HTML segments
    """

    #: The current HTML segment
    segment: HtmlElement

    # pylint: disable=super-init-not-called
    def __init__(self, segment: HtmlElement) -> None:
        """
        Convert the lxml tree element to a flat text string.
        Preserve <br> tags as new lines characters.
        Remove all inner tags but keep their text content.
        Unescape all special HTML entities into unicode characters.

        :param segment: The current HTML segment
        """
        self.segment = segment
        # Preserve new line tags
        for br in self.segment.iter("br"):
            br.tail = "\n" + br.tail if br.tail else "\n"
        # Strip all inner tags
        strip_tags(self.segment, "*")
        # Unescape to convert umlauts etc. to unicode
        self.text = unescape(self.segment.text_content()).strip()

    def translate(self, translated_text: str) -> None:
        """
        Translate the current HTML segment and create new sub elements for line breaks

        :param translated_text: The translated text
        """
        # Only do something if response was not empty (otherwise keep original text)
        if translated_text:
            # Split the text by newlines characters
            lines = translated_text.splitlines()
            # Take the first line as initial text
            self.segment.text = lines[0]
            # If there are more than one line returned, insert <br> tags
            for line in lines[1:]:
                SubElement(self.segment, "br").tail = line


class HTMLField:
    """
    A class for more complex HTML fields which are splitted into segments
    """

    #: The name of the corresponding model field
    name: str
    #: The list of HTML segments
    segments: list[HtmlElement] = []
    #: The current HTML stream
    html: HtmlElement = None

    def __init__(self, name: str, translation: PageTranslation) -> None:
        """
        Parse the HTML string into an lxml tree object and split into segments

        :param html: The HTML string content of this field
        """
        self.name = name
        if html_str := getattr(translation, name, ""):
            self.html = fromstring(html_str)
            # Translate all specified tags (and filter out empty segments)
            self.segments = [
                HTMLSegment(segment=segment)
                for segment in self.html.iter(*settings.SUMM_AI_HTML_TAGS)
            ]

    def __repr__(self) -> str:
        """
        The representation used for logging

        :return: The canonical string representation of the HTML field
        """
        return f"<HTMLField (segments: {self.segments})>"

    @property
    def translated_text(self) -> str | None:
        """
        Assemble the content of the HTML segments into a HTML string again

        :returns: The translated HTML
        """
        if self.html is not None:
            return tostring(
                self.html, encoding="unicode", method="html", pretty_print=True
            )
        return None

    @property
    def exception(self) -> SummAiException | None:
        """
        Check if any of the segments experienced an error

        :returns: The first exception of this HTML field
        """
        return next(
            (segment.exception for segment in self.segments if segment.exception), None
        )


class TranslationHelper:
    """
    Custom helper class for interaction with SUMM.AI

    :param request: The current request
    :param form_class: The subclass of the current content type
    :param object_instance: The current object instance to be translated
    :param german_translation: The German source translation of the object instance
    :param valid: Wether or not the translation was successful
    :param text_fields: The text fields of this helper
    :param html_fields: The HTML fields of this helper
    """

    #: Wether or not the translation was successful
    valid: bool = True

    def __init__(
        self,
        request: HttpRequest,
        form_class: ModelFormMetaclass,
        object_instance: Page,
    ) -> None:
        """
        Constructor initializes the class variables

        :param request: current request
        :param form_class: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
                           subclass of the current content type
        :param object_instance: The current object instance
        """
        self.request: HttpRequest = request
        self.form_class: ModelFormMetaclass = form_class
        self.object_instance: AbstractContentModel = object_instance
        self.german_translation: AbstractContentTranslation | None = (
            object_instance.get_translation(settings.SUMM_AI_GERMAN_LANGUAGE_SLUG)
        )
        if not self.german_translation:
            messages.error(
                self.request,
                _('No German translation could be found for {} "{}".').format(
                    type(object_instance)._meta.verbose_name.title(),
                    object_instance.best_translation.title,
                ),
            )
            self.valid = False
            return
        self.text_fields: list[TextField] = [
            TextField(name=text_field, translation=self.german_translation)
            for text_field in settings.SUMM_AI_TEXT_FIELDS
        ]
        self.html_fields: list[HTMLField] = [
            HTMLField(name=html_field, translation=self.german_translation)
            for html_field in settings.SUMM_AI_HTML_FIELDS
        ]

    @property
    def fields(self) -> list[HTMLField | TextField]:
        """
        Get all fields of this helper instance

        :returns: All fields which need to be translated
        """
        return self.text_fields + self.html_fields

    def get_text_fields(self) -> list[HTMLSegment]:
        """
        Get all text fields of this helper instance
        (all native :attr:`~integreat_cms.summ_ai_api.utils.TranslationHelper.text_fields`
        combined with all segments of all
        :attr:`~integreat_cms.summ_ai_api.utils.TranslationHelper.html_fields`)

        :returns: All text fields and segments which need to be translated
        """
        if not self.valid:
            return []
        text_fields = list(
            filter(
                # Filter out empty texts
                lambda x: x.text,
                itertools.chain(
                    # Get all plain text fields
                    self.text_fields,
                    # Get all segments of all HTML fields
                    *[html_field.segments for html_field in self.html_fields],
                ),
            )
        )
        logger.debug(
            "Text fields for %r: %r",
            self,
            text_fields,
        )
        return text_fields

    def commit(self, easy_german: Language) -> bool:
        """
        Save the translated changes to the database

        :param easy_german: The language object of Easy German
        :return: Whether the commit was successful
        """
        if not self.valid:
            return False
        if TYPE_CHECKING:
            assert self.german_translation
        # Check whether any of the fields returned an error
        if any(field.exception for field in self.fields):
            return False
        # Initialize form to create new translation object
        existing_target_translation = self.object_instance.get_translation(
            settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG
        )
        content_translation_form = self.form_class(
            data={
                # Pass all inherited fields
                **{
                    field_name: getattr(self.german_translation, field_name, "")
                    for field_name in settings.SUMM_AI_INHERITED_FIELDS
                },
                # Pass all translated texts as data values
                **{field.name: field.translated_text for field in self.fields},
                # Always set automatic translations into pending review state
                "status": status.REVIEW,
                "machine_translated": True,
                "currently_in_translation": False,
            },
            instance=existing_target_translation,
            additional_instance_attributes={
                "creator": self.request.user,
                "language": easy_german,
                self.german_translation.foreign_field(): self.object_instance,
            },
        )
        # Validate translation form
        if not content_translation_form.is_valid():
            logger.error(
                "Automatic translation into Easy German for %r could not be created because of %s",
                self.object_instance,
                content_translation_form.errors,
            )
            return False
        # Save new translation
        content_translation_form.save()
        # Revert "currently in translation" value of all versions
        if existing_target_translation:
            if settings.REDIS_CACHE:
                existing_target_translation.all_versions.invalidated_update(
                    currently_in_translation=False
                )
            else:
                existing_target_translation.all_versions.update(
                    currently_in_translation=False
                )

        logger.debug(
            "Successfully translated %r into Easy German",
            content_translation_form.instance,
        )
        return True

    def __repr__(self) -> str:
        """
        The representation used for logging

        :return: The canonical string representation of the translation helper
        """
        return f"<TranslationHelper (translation: {self.german_translation!r})>"


T = TypeVar("T")


class PatientTaskQueue(deque, Generic[T]):
    """
    A 'patient' task queue which only hands out sleep tasks after a task was reported as failed.

    :param last_rate_limit: The UNIX timestamp when the last rate limited request occurred
    :param wait_time: Seconds to wait after running into the rate limit before sending the next requests
    :param max_retries: Maximum amount of retries for a string to translate before giving up
    :param tasks: List of request tasks
    :param abort_function: Function to call for each unfinished task if the queue is aborted
    """

    #: The UNIX timestamp when the last rate limited request occurred
    last_rate_limit: float | None = None

    #: Seconds to wait after running into the rate limit before sending the next requests
    wait_time: float = settings.SUMM_AI_RATE_LIMIT_COOLDOWN

    #: Maximum amount of retries for a string to translate before giving up
    max_retries: int = settings.SUMM_AI_MAX_RETRIES

    def __init__(
        self,
        tasks: list[T],
        wait_time: float = settings.SUMM_AI_RATE_LIMIT_COOLDOWN,
        max_retries: int = settings.SUMM_AI_MAX_RETRIES,
        abort_function: Callable | None = None,
    ) -> None:
        """
        Constructor initializes the class variables

        :param tasks: List of request tasks
        :param wait_time: Waiting time until start next request in seconds
        :param max_retries: Maximum retries before giving up
        :param abort_function: Function to call for each unfinished task if the queue is aborted.
                               Takes two arguments: The task (:class:`asyncio.Future`) and the reason given (:class:`str`).
                               Can be `None` instead to do nothing.
        """
        super().__init__(tasks)
        self.wait_time = wait_time
        self.max_retries = max_retries
        self.retries = 0
        self.abort_function = abort_function
        # Whether queue processing was aborted
        self._aborted = False
        # Tasks handed out to workers. If we get a report about a task that completed or hit the rate limit and it's not in this list,
        # or if all workers finish and this list is not empty, something went wrong.
        self._in_progress: list[T] = []

    def __aiter__(self) -> PatientTaskQueue[T]:
        return self

    async def __anext__(self) -> T:
        """
        Checks if the queue processing should wait.
        Ejects the next task or goes to sleep until the end of the waiting time.

        :returns: a task of the queue
        """
        if self._aborted:
            raise StopAsyncIteration

        now: float = time.time()
        if (
            self.last_rate_limit is not None
            and (wait_time_remaining := self.wait_time - (now - self.last_rate_limit))
            > 0
        ):
            # Bail out early when the queue is empty
            if not self:
                raise StopAsyncIteration
            # If we are currently waiting out a rate limit,
            # sleep for the remaining time before handing out the next task.
            logger.debug(
                "PatientTaskQueue hit rate limit previously (blocking for another %ss)",
                wait_time_remaining,
            )
            await asyncio.sleep(wait_time_remaining)
        try:
            task = self.popleft()
            self._in_progress.append(task)
            return task
        except IndexError as e:
            raise StopAsyncIteration from e

    def hit_rate_limit(self, task: T) -> None:
        """
        A task hit the rate limit, so wait a bit and reschedule the task

        :param task: The task that failed because of the rate limiting
        """
        assert (
            task in self._in_progress
        ), f"PatientTaskQueue: Failed task not known as in progress: {task}"

        # Only save current timestamp if this is the first failed request reported
        if (
            self.last_rate_limit is None
            or time.time() - self.last_rate_limit > self.wait_time
        ):
            self.last_rate_limit = time.time()
            self.retries += 1
            logger.debug(
                "PatientTaskQueue hit rate limit during %r (blocking for %ss, %s/%s retries)",
                task,
                self.wait_time,
                self.retries - 1,
                self.max_retries,
            )
        else:
            logger.debug(
                "PatientTaskQueue hit rate limit during %r (already known, %s/%ss elapsed)",
                task,
                time.time() - self.last_rate_limit,
                self.wait_time,
            )

        # Reschedule the failed task
        self._in_progress.remove(task)
        self.appendleft(task)

        if self.retries > self.max_retries and not self._aborted:
            self.abort(
                f"Retried tasks a consecutive {self.max_retries} times. Giving up."
            )

    def completed(self, task: T) -> None:
        """
        A task was completed, reset the retry counter

        :param task: The task that failed because of the rate limiting
        """
        assert (
            task in self._in_progress
        ), f"PatientTaskQueue: Completed task not known as in progress: {task}"

        self.retries = 0
        self._in_progress.remove(task)

    def abort(self, reason: str = "Aborted") -> None:
        """
        Abort the Queue, handling unfinished task according to the supplied abort function.

        :param reason: The reason why the queue was aborted that is to be handed to the supplied abort function.
        """
        self._aborted = True
        logger.debug("PatientTaskQueue aborted: %s", reason)
        if self.abort_function:
            for unfinished_task in list(self) + self._in_progress:
                self.abort_function(unfinished_task, reason)


async def worker(
    loop: asyncio.AbstractEventLoop,
    task_generator: PatientTaskQueue[partial],
    identifier: str,
) -> list[Any]:
    """
    Continuously gets a task from the queue and executes it.
    Stops once no more tasks are available.
    This form makes it easy to always have at most n concurrent tasks
    as well as intermittent wait times through the task generator.

    Catches :class:`~integreat_cms.summ_ai_api.utils.SummAiRateLimitingExceeded` and :class:`~integreat_cms.summ_ai_api.utils.SummAiInvalidJSONError` and counts them as rate limit hits in order enqueue them again.

    :param loop: The asyncio event loop to execute tasks in
    :param task_generator: Queue to execute tasks from
    :param identifier: Identifyer of the worker (for logging purposes)
    :returns: A list of task-results
    """
    logger.debug("Worker #%s initialized", identifier)

    completed: list[Any] = []
    async for task in task_generator:
        try:
            result = await loop.create_task(task())
        except (SummAiRateLimitingExceeded, SummAiInvalidJSONError):
            task_generator.hit_rate_limit(task)
        else:
            task_generator.completed(task)
            completed.append(result)

    logger.debug("Worker #%s completed %s tasks", identifier, len(completed))
    return completed
