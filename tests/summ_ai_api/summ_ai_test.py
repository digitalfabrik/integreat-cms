from __future__ import annotations

import asyncio
import time
from functools import partial
from typing import TYPE_CHECKING, TypeVar

import aiohttp
import pytest
from django.test.client import AsyncClient
from django.urls import reverse

from integreat_cms.cms.forms import PageTranslationForm
from integreat_cms.cms.models.pages.page_translation import PageTranslation
from integreat_cms.cms.utils.stringify_list import iter_to_string
from integreat_cms.summ_ai_api.summ_ai_api_client import (
    SummAiApiClient,
    SummAiInvalidJSONError,
    SummAiRateLimitingExceeded,
    SummAiRuntimeError,
)
from integreat_cms.summ_ai_api.utils import (
    HTMLField,
    PatientTaskQueue,
    TextField,
    worker,
)

from ..conftest import (
    ANONYMOUS,
    APP_TEAM,
    CMS_TEAM,
    PRIV_STAFF_ROLES,
    ROOT,
    SERVICE_TEAM,
)
from ..utils import assert_message_in_log
from .utils import (
    enable_summ_api,
    get_changed_pages,
    make_mock_summ_ai_server,
    make_mock_summ_ai_server_rate_limited,
    make_rogue_summ_ai_server,
    MockedRequest,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Final

    from _pytest.logging import LogCaptureFixture
    from pytest_django.fixtures import SettingsWrapper

# pylint: disable=global-statement

# Mapping between roles and pages used in the tests
# to avoid simultaneous translation of the same content by different users
role_pages_mapping: Final[dict[str, list[int]]] = {
    ROOT: [1, 2],
    APP_TEAM: [3, 4],
    SERVICE_TEAM: [5],
    CMS_TEAM: [6],
}


attempts: dict


def test_worker() -> None:
    """
    Test that the worker properly works through tasks from the
    PatientTaskQueue, returning the results.
    """

    async def works(msg: str) -> str:
        return msg

    global attempts
    attempts = {}

    async def fails_on_first_attempt(msg: str) -> str:
        if msg not in attempts:
            attempts[msg] = 0
        attempts[msg] += 1
        if attempts[msg] < 2:
            raise SummAiRateLimitingExceeded
        return msg

    tasks = [
        partial(works, "1"),
        partial(fails_on_first_attempt, "2"),
        partial(works, "3"),
        partial(fails_on_first_attempt, "4"),
        partial(works, "5"),
    ]
    task_generator = PatientTaskQueue(tasks, 0.1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    result = loop.run_until_complete(worker(loop, task_generator, "0-test"))

    assert set(result) == {"1", "2", "3", "4", "5"}


async def test_translate_text_field_successful_translation(
    settings: SettingsWrapper, aiohttp_raw_server: Callable, caplog: LogCaptureFixture
) -> None:
    """
    :param settings: The Django settings
    :param aiohttp_raw_server: The fixture providing the dummy aiohttp server used for faking the SUMM.AI API server
    :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
    """
    session = aiohttp.ClientSession()
    fake_server = await aiohttp_raw_server(
        make_mock_summ_ai_server(
            response_data={
                "translated_text": "a text",
                "jobid": "9999",
            },
            status=200,
        )
    )
    # Redirect call to the SUMM.AI API to the fake server
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )

    my_api_client = SummAiApiClient(MockedRequest(), PageTranslationForm)
    text_field = TextField("content", PageTranslation(content="ein Text"))
    assert text_field.text == "ein Text"

    translated_text_field = await my_api_client.translate_text_field(
        session, text_field
    )

    assert translated_text_field is text_field
    assert translated_text_field.translated_text == "a text"
    # we check that the origin text is not changed
    assert translated_text_field.text == "ein Text"

    # The same with an HTMLField as well
    html_field = HTMLField("content", PageTranslation(content="<p>ein <b>Text</b></p>"))

    translated_html_segments = [
        await my_api_client.translate_text_field(session, segment)
        for segment in html_field.segments
    ]

    assert set(translated_html_segments) == set(html_field.segments)
    assert html_field.translated_text == "<p>a text</p>\n"

    await session.close()


async def test_translate_text_field_hit_rate_limit(
    settings: SettingsWrapper, aiohttp_raw_server: Callable, caplog: LogCaptureFixture
) -> None:
    """
    see :func:`~test_translate_text_field_successful_translation`
    """
    session = aiohttp.ClientSession()
    my_api_client = SummAiApiClient(MockedRequest(), PageTranslationForm)
    text_field = TextField("content", PageTranslation(content="ein Text"))
    fake_server = await aiohttp_raw_server(
        make_mock_summ_ai_server(
            response_data={
                "error": "Too many requests. Please wait and resend your request.",
            },
            status=429,
        )
    )
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )

    with pytest.raises(SummAiRateLimitingExceeded):
        await my_api_client.translate_text_field(session, text_field)
    await session.close()


async def test_translate_text_field_ddos_defense(
    settings: SettingsWrapper, aiohttp_raw_server: Callable, caplog: LogCaptureFixture
) -> None:
    """
    see :func:`~test_translate_text_field_successful_translation`
    """
    session = aiohttp.ClientSession()
    my_api_client = SummAiApiClient(MockedRequest(), PageTranslationForm)
    text_field = TextField("content", PageTranslation(content="ein Text"))
    fake_server = await aiohttp_raw_server(
        make_mock_summ_ai_server(
            response_data={
                "error": "Too many requests. Please wait and resend your request.",
            },
            status=529,
        )
    )
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )

    with pytest.raises(SummAiRateLimitingExceeded):
        await my_api_client.translate_text_field(session, text_field)
    await session.close()


async def test_translate_text_field_internal_server_error(
    settings: SettingsWrapper, aiohttp_raw_server: Callable, caplog: LogCaptureFixture
) -> None:
    """
    see :func:`~test_translate_text_field_successful_translation`
    """
    session = aiohttp.ClientSession()
    my_api_client = SummAiApiClient(MockedRequest(), PageTranslationForm)
    text_field = TextField("content", PageTranslation(content="ein Text"))
    # get a fresh log to test
    caplog.clear()
    fake_server = await aiohttp_raw_server(
        make_mock_summ_ai_server(
            response_data={
                "error": "An error occurred",
                "jobid": "9999",
            },
            status=500,
        )
    )
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )
    await my_api_client.translate_text_field(session, text_field)

    errors = tuple(
        (record.message for record in caplog.records if record.levelname == "ERROR")
    )
    assert (
        "SUMM.AI translation of <TextField (text: ein Text)> failed because of <class 'integreat_cms.summ_ai_api.utils.SummAiRuntimeError'>: API has internal server error"
        in errors
    )
    await session.close()


async def test_translate_text_forbidden(
    settings: SettingsWrapper, aiohttp_raw_server: Callable, caplog: LogCaptureFixture
) -> None:
    """
    tests 403 response
    see :func:`~test_translate_text_field_successful_translation`
    """
    session = aiohttp.ClientSession()
    my_api_client = SummAiApiClient(MockedRequest(), PageTranslationForm)
    text_field = TextField("content", PageTranslation(content="ein Text"))

    # get a fresh log to test
    caplog.clear()
    fake_server = await aiohttp_raw_server(
        make_mock_summ_ai_server(
            response_data={
                "jobid": "9999",
            },
            status=403,
        )
    )
    # Redirect call to the SUMM.AI API to the fake server
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )
    await my_api_client.translate_text_field(session, text_field)

    errors = tuple(
        (record.message for record in caplog.records if record.levelname == "ERROR")
    )
    assert len(errors) >= 1
    assert (
        "SUMM.AI translation of <TextField (text: ein Text)> failed because of <class 'integreat_cms.summ_ai_api.utils.SummAiRuntimeError'>: Unexpected API result: 403 - {'jobid': '9999'}"
        in errors
    )
    await session.close()


async def test_translate_text_with_empty_text_field(
    settings: SettingsWrapper, aiohttp_raw_server: Callable, caplog: LogCaptureFixture
) -> None:
    """
    see :func:`~test_translate_text_field_successful_translation`
    """
    session = aiohttp.ClientSession()
    my_api_client = SummAiApiClient(MockedRequest(), PageTranslationForm)
    text_field = TextField("content", PageTranslation(content="ein Text"))
    session = aiohttp.ClientSession()
    caplog.clear()
    fake_server = await aiohttp_raw_server(
        make_mock_summ_ai_server(
            response_data={
                "translated_text": "a text",
                "jobid": "9999",
            },
            status=200,
        )
    )
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )
    text_field.text = ""
    with pytest.raises(SummAiRuntimeError):
        await my_api_client.translate_text_field(session, text_field)
    await session.close()


@pytest.mark.django_db
async def test_auto_translate_easy_german(
    login_role_user_async: tuple[AsyncClient, str],
    settings: SettingsWrapper,
    aiohttp_server: Callable,
    caplog: LogCaptureFixture,
) -> None:
    """
    This test checks whether the SUMM.AI API client works as expected

    :param login_role_user_async: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param aiohttp_server: The fixture providing the dummy aiohttp server used for faking the SUMM.AI API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # The region we want to use for testing
    region_slug = "augsburg"
    # Enable SUMM.AI in the test region
    await enable_summ_api(region_slug)
    # Setup a dummy server to fake responses from the SUMM.AI API server (an instance of aiohttp.test_utils.RawTestServer)
    fake_server = await aiohttp_server(make_mock_summ_ai_server_rate_limited())
    # Redirect call to the SUMM.AI API to the fake server
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )
    # Reduce rate limiting timeout
    settings.SUMM_AI_RATE_LIMIT_COOLDOWN = 0.5
    # Test for english messages
    settings.LANGUAGE_CODE = "en"
    # Log the user in
    client, role = login_role_user_async
    # Translate the pages
    selected_ids = role_pages_mapping.get(role, [1])

    translate_easy_german = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": region_slug,
            "language_slug": settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG,
        },
    )
    response = await client.post(
        translate_easy_german, data={"selected_ids[]": selected_ids}
    )
    print(response.headers)
    if role in PRIV_STAFF_ROLES:
        # If the role should be allowed to access the view, we expect a successful result
        assert response.status_code == 302
        page_tree = reverse(
            "pages",
            kwargs={
                "region_slug": region_slug,
                "language_slug": settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG,
            },
        )
        assert response.headers.get("Location") == page_tree
        response = await client.get(page_tree)
        print(response.headers)
        # Get the page objects including their translations from the database
        changed_pages = await get_changed_pages(settings, selected_ids)
        # Check that the success message are present
        if len(changed_pages) == 1:
            assert_message_in_log(
                f'SUCCESS  Page "{changed_pages[0][settings.SUMM_AI_GERMAN_LANGUAGE_SLUG]}" has been successfully translated into Easy German.',
                caplog,
            )
        else:
            changed_pages_str = iter_to_string(
                page[settings.SUMM_AI_GERMAN_LANGUAGE_SLUG] for page in changed_pages
            )
            assert_message_in_log(
                f"SUCCESS  The following pages have been successfully translated into Easy German: {changed_pages_str}",
                caplog,
            )
        # Check that the page translation exists and really has the correct content
        for page in changed_pages:
            assert (
                "Hier ist Ihre Leichte Sprache Übersetzung"
                in page[settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG].content
            )
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={translate_easy_german}"
        )
    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
async def test_summ_ai_error_handling(
    login_role_user_async: tuple[AsyncClient, str],
    settings: SettingsWrapper,
    aiohttp_raw_server: Callable,
    caplog: LogCaptureFixture,
) -> None:
    """
    This test checks whether the error handling of the SUMM.AI API client works as expected.

    :param login_role_user_async: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param aiohttp_raw_server: The fixture providing the dummy aiohttp server used for faking the SUMM.AI API server
    :param caplog: The :fixture:`caplog` fixture
    """
    # The region we want to use for testing
    region_slug = "augsburg"
    # Setup a dummy server to fake responses from the SUMM.AI API server (an instance of aiohttp.test_utils.RawTestServer)
    fake_server = await aiohttp_raw_server(
        make_mock_summ_ai_server(
            response_data={
                "error": "An error occurred",
            },
            status=500,
        )
    )
    # Enable SUMM.AI in the test region
    await enable_summ_api(region_slug)
    # Redirect call to the SUMM.AI API to the fake server
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )

    # Test for english messages
    settings.LANGUAGE_CODE = "en"
    # Log the user in
    client, role = login_role_user_async
    # Translate the pages
    translate_easy_german = reverse(
        "machine_translation_pages",
        kwargs={
            "region_slug": region_slug,
            "language_slug": settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG,
        },
    )

    ready_for_mt_page_id = 14
    response = await client.post(
        translate_easy_german, data={"selected_ids[]": [ready_for_mt_page_id]}
    )
    print(response.headers)

    if role in PRIV_STAFF_ROLES:
        # If the role should be allowed to access the view, we expect a redirect to the page tree
        assert response.status_code == 302
        page_tree = reverse(
            "pages",
            kwargs={
                "region_slug": region_slug,
                "language_slug": settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG,
            },
        )
        assert response.headers.get("Location") == page_tree
        response = await client.get(page_tree)
        print(response.headers)
        # Check that the error message is present
        assert_message_in_log(
            'ERROR    Page "Behörden und Beratung" could not be automatically translated into Easy German.',
            caplog,
        )


def test_validate_response_valid() -> None:
    """
    Test for validate_response method.
    Should return True when 'translated_text' is found in request.
    """
    response_data_translation_succeeded = {
        "dummy": "dummy",
        "translated_text": "Das ist einfaches Deutsch.",
    }
    assert (
        SummAiApiClient(MockedRequest(), PageTranslationForm).validate_response(
            response_data_translation_succeeded, 200
        )
        is True
    ), "if translated_text found in reponse-data, validate_response should return True"


def test_validate_response_invalid() -> None:
    """
    Test for validate_response method.
    Should throw exception when 'translated_text' is not found in request.
    """
    response_data_translation_failed = {
        "dummy": "dummy",
        "error": "no translation test error",
    }
    with pytest.raises(SummAiRuntimeError):
        SummAiApiClient(MockedRequest(), PageTranslationForm).validate_response(
            response_data_translation_failed, 200
        )


async def test_unexpected_html(
    settings: SettingsWrapper, aiohttp_raw_server: Callable
) -> None:
    """
    Test correct handling for an unexpected HTML response by SUMM.AI.
    Tests if SummAiInvalidJSONError is raised when unexpected HTML is sent as response.
    """
    session = aiohttp.ClientSession()
    fake_server = await aiohttp_raw_server(
        make_rogue_summ_ai_server(
            response_text="""
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>500 Internal Server Error</title>
</head><body>
<h1>Internal Server Error</h1>
<p>The server encountered an internal error or
misconfiguration and was unable to complete
your request.</p>
<p>Please contact the server administrator at
 webmaster@localhost to inform them of the time this error occurred,
 and the actions you performed just before this error.</p>
<p>More information about this error may be available
in the server error log.</p>
<hr>
<address>Apache/2.4.41 (Ubuntu) Server at localhost Port 8080</address>
</body></html>
            """,
            status=200,
        )
    )
    # Redirect call to the SUMM.AI API to the fake server
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )

    my_api_client = SummAiApiClient(MockedRequest(), PageTranslationForm)
    text_field = TextField("content", PageTranslation(content="ein Text"))

    with pytest.raises(SummAiInvalidJSONError):
        await my_api_client.translate_text_field(session, text_field)


async def test_missing_translation(
    settings: SettingsWrapper, aiohttp_raw_server: Callable
) -> None:
    """
    Test correct handling for a json response without the translated_text key by SUMM.AI.
    Tests if SummAiRuntimeError is raised when invalid JSON is sent as response.
    """
    response_data_translation_missing = {
        "dummy": "dummy",
    }
    with pytest.raises(SummAiRuntimeError):
        SummAiApiClient(MockedRequest(), PageTranslationForm).validate_response(
            response_data_translation_missing, 200
        )


def test_check_rate_limit_exceeded(
    settings: SettingsWrapper, caplog: LogCaptureFixture
) -> None:
    """
    Test for check_rate_limit_exceeded method. Tests if return is True when
    response-status = 429 (too many requests) or 529 (site overloaded),
    otherwise False

    :param settings: The Django settings

    :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
    """

    assert (
        SummAiApiClient(MockedRequest(), PageTranslationForm).check_rate_limit_exceeded(
            200
        )
        is False
    ), "if response-status not in (429, 529), check-rate-limit should return False"
    with pytest.raises(SummAiRateLimitingExceeded):
        SummAiApiClient(MockedRequest(), PageTranslationForm).check_rate_limit_exceeded(
            429
        )
    with pytest.raises(SummAiRateLimitingExceeded):
        SummAiApiClient(MockedRequest(), PageTranslationForm).check_rate_limit_exceeded(
            529
        )

    errors = tuple(
        (record.message for record in caplog.records if record.levelname == "ERROR")
    )
    assert len(errors) >= 2
    assert (
        f"SUMM.AI translation is waiting for {settings.SUMM_AI_RATE_LIMIT_COOLDOWN}s because the rate limit has been exceeded"
        in errors
    ), "after check_rate_limit_exceeded() with 429 or 529, a logging entry should appear"

    assert (
        SummAiApiClient(MockedRequest(), PageTranslationForm).check_rate_limit_exceeded(
            500
        )
        is False
    ), "if response-status not in (429, 529), check-rate-limit should return False"


async def test_patient_task_queue_normal_deque() -> None:
    """
    Test for PatientTaskQueue Class. Tests that a first-in/first out (fifo) deque-queue is built from a task-list
    Checks that __anext__() removes one element each from the queue
    """

    tasks = [1, 2, 3]
    task_generator = PatientTaskQueue(tasks, 1)

    # we check that list comes reverse (fifo-queue)
    i = 0
    async for task in task_generator:
        assert task == tasks[i]
        i += 1

    assert not task_generator
    # we check that __anext__() did remove elements from the queue
    with pytest.raises(StopAsyncIteration):
        await anext(task_generator)


# pylint: disable=comparison-with-callable
async def test_patient_task_queue_hit_rate_limit() -> None:
    """
    Test for PatientTaskQueue Class. It tests that when the maximum number of parallel requests
    to the summ_ai_api has been exceeded (rate limit exceeded), a defined time is waited until the next task object is returned via __anext__().
    """

    T = TypeVar("T")

    async def identity(x: T) -> T:
        return x

    tasks = [
        partial(identity, 1),
        partial(identity, 2),
        partial(identity, 3),
    ]
    # for the test, waiting-time is reduced to 0.5s, default is defined in settings.SUMM_AI_RATE_LIMIT_COOLDOWN
    task_generator = PatientTaskQueue(tasks, wait_time=0.5)

    # Test first task
    task = await anext(task_generator)
    assert task == tasks[0], "PatientTaskQueue should return the first element"

    # Test second task with timing
    start = time.time()
    task = await anext(task_generator)
    end = time.time()
    assert task == tasks[1], "PatientTaskQueue should return the second element"
    assert (
        end - start < 0.5
    ), "PatientTaskQueue should return the second element very fast"

    # Hit the rate limit and check whether the second task is rescheduled
    task_generator.hit_rate_limit(task)
    start = time.time()
    task = await anext(task_generator)
    end = time.time()
    assert task == tasks[1], "PatientTaskQueue should return the second element again"
    assert end - start > 0.5, "PatientTaskQueue should return the second element slower"

    # Test third task
    start = time.time()
    task = await anext(task_generator)
    end = time.time()
    assert task == tasks[2], "PatientTaskQueue should return the third element"
    assert (
        end - start < 0.5
    ), "PatientTaskQueue should return the third element very fast"

    assert (
        not task_generator
    ), "PatientTaskQueue should be empty after three tasks have been removed"


# pylint: disable=comparison-with-callable
async def test_patient_task_queue_max_retries() -> None:
    """
    Test for PatientTaskQueue Class. Tests that it stops early
    when requests are not successful after a cooldown, resulting in another cooldown repeatedly.
    """

    T = TypeVar("T")

    async def identity(x: T) -> T:
        return x

    tasks = [
        partial(identity, 1),
        partial(identity, 2),
        partial(identity, 3),
    ]
    # for the test, waiting_time is reduced to 0.5s, default is defined in settings.SUMM_AI_RATE_LIMIT_COOLDOWN
    # max_retries is reduced to 3, default is defined in settings.SUMM_AI_MAX_RETRIES
    task_generator = PatientTaskQueue(tasks, wait_time=0.5, max_retries=2)

    # Test first task
    task = await anext(task_generator)
    assert task == tasks[0], "PatientTaskQueue should return the first element"

    # Hit the rate limit, first retry
    task_generator.hit_rate_limit(task)
    task = await anext(task_generator)
    assert task == tasks[0], "PatientTaskQueue should return the first element again"

    # Report that task was successful to reset the retry count
    task_generator.completed(task)
    task = await anext(task_generator)
    assert task == tasks[1], "PatientTaskQueue should return the second element"

    # Hit the rate limit, first retry again
    task_generator.hit_rate_limit(task)
    task = await anext(task_generator)
    assert task == tasks[1], "PatientTaskQueue should return the second element again"

    # Hit the rate limit, second retry
    task_generator.hit_rate_limit(task)
    task = await anext(task_generator)
    assert (
        task == tasks[1]
    ), "PatientTaskQueue should return the second element for the third time"

    # Hit the rate limit, there should be no more retries
    task_generator.hit_rate_limit(task)
    with pytest.raises(StopAsyncIteration):
        task = await anext(task_generator)

    assert (
        len(task_generator) == 2
    ), "PatientTaskQueue should have two tasks left that could not be completed"
    assert set(task_generator) == {
        tasks[1],
        tasks[2],
    }, "PatientTaskQueue should have the second and third task left as they could not be completed"
