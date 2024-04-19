from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from typing import Any
    from pytest_django.fixtures import SettingsWrapper
    from requests_mock.mocker import Mocker
    from requests_mock.request import _RequestObjectProxy
    from requests_mock.response import _Context
    from _pytest.logging import LogCaptureFixture

import pytest
from django.core.exceptions import ImproperlyConfigured

from integreat_cms.cms.models import PushNotification, Region
from integreat_cms.firebase_api.firebase_api_client import FirebaseApiClient


class TestFirebaseApiClient:
    """
    Test for :class:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient`

    Only tests the correct result (``True``/``False``) and logging output depending on the firebase-HTTP response.
    It does not test if firebase-api-server works/answers as expected.
    """

    #: A set of response-data for the mocking-function
    #: Google does not really document what errors are possible
    response_mock_data = {
        "200_success": {
            "name": "projects/integreat-2020/messages/1",
            "status_code": 200,
        },
        "200_no_name": {"status_code": 200},
        "401_invalid_key": {
            "error": {
                "message": "Request had invalid authentication credentials.",
                "code": 401,
            },
            "status_code": 401,
        },
        "404": {"error": {"code": 404}, "status_code": 404},
    }

    def __init__(self) -> None:
        self.patch: Any = None

    def setup_method(self) -> None:
        self.patch = patch.object(
            FirebaseApiClient, "_get_access_token", return_value="secret access token"
        )
        self.patch.start()

    def teardown_method(self) -> None:
        self.patch.stop()
        self.patch = None

    @pytest.mark.django_db
    def test_client_throws_exception_when_fcm_disabled(
        self, settings: SettingsWrapper, load_test_data: None
    ) -> None:
        """
        Tests that an ImproperlyConfigured exception is thrown, if firebase API is disabled in settings

        :param settings: The Django settings
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        """
        settings.FCM_ENABLED = False
        notification = PushNotification.objects.first()
        with pytest.raises(ImproperlyConfigured):
            FirebaseApiClient(notification)

    @pytest.mark.django_db
    def test_is_valid(self, settings: SettingsWrapper, load_test_data: None) -> None:
        """
        Tests that :meth:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient.is_valid` is ``True``,
        when FCM_ENABLED and pushNotification valid (with title and translation)

        :param settings: The Django settings
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        """
        settings.FCM_ENABLED = True
        notification = PushNotification.objects.first()
        assert FirebaseApiClient(notification).is_valid()

    @pytest.mark.django_db
    def test_is_invalid_when_no_translation(
        self, settings: SettingsWrapper, load_test_data: None
    ) -> None:
        """
        Tests that :meth:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient.is_valid` is ``False``,
        when translation missing

        :param settings: The Django settings
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        """
        settings.FCM_ENABLED = True
        notification = PushNotification.objects.first()
        pns = FirebaseApiClient(notification)
        pns.prepared_pnts = []
        assert not pns.is_valid()

    @pytest.mark.django_db
    def test_is_invalid_when_no_title(
        self, settings: SettingsWrapper, load_test_data: None
    ) -> None:
        """
        Tests that :meth:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient.is_valid` is ``False``,
        when pushNotification-title is missing

        :param settings: The Django settings
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        """
        settings.FCM_ENABLED = True
        notification = PushNotification.objects.first()
        pns = FirebaseApiClient(notification)
        pns.prepared_pnts[0].title = ""
        assert not pns.is_valid()

    @pytest.mark.django_db
    def test_firebase_api_200_success(
        self,
        settings: SettingsWrapper,
        load_test_data: None,
        requests_mock: Mocker,
        caplog: LogCaptureFixture,
    ) -> None:
        """
        Tests firebase-api-response handling, test a successful API call

        :param settings: The Django settings
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
        """
        status = self.send_all_with_mocked_response(
            settings, requests_mock, self.response_mock_data["200_success"]
        )
        for record in caplog.records:
            assert (
                "sent, FCM id: 'projects/integreat-2020/messages/1'" in record.message
            )
        assert status

    @pytest.mark.django_db
    def test_firebase_api_200_unexpected_api_response(
        self,
        settings: SettingsWrapper,
        load_test_data: None,
        requests_mock: Mocker,
        caplog: LogCaptureFixture,
    ) -> None:
        """
        Tests firebase-api-response handling,
        test a partial successful api call - HTTP 200 but no message name in response

        :param settings: The Django settings
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
        """
        status = self.send_all_with_mocked_response(
            settings, requests_mock, self.response_mock_data["200_no_name"]
        )
        for record in caplog.records:
            assert "sent, but unexpected API response" in record.message
        assert status

    @pytest.mark.django_db
    def test_firebase_api_403_wrong_token(
        self,
        settings: SettingsWrapper,
        load_test_data: None,
        requests_mock: Mocker,
        caplog: LogCaptureFixture,
    ) -> None:
        """
        Tests firebase-api-response handling,
        test a denied call - HTTP 403 because of wrong auth-token

        :param settings: The Django settings
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
        """
        status = self.send_all_with_mocked_response(
            settings, requests_mock, self.response_mock_data["401_invalid_key"]
        )
        for record in caplog.records:
            assert "Received invalid response from FCM for" in record.message
        assert not status

    @pytest.mark.django_db
    def test_firebase_api_404(
        self,
        settings: SettingsWrapper,
        load_test_data: None,
        requests_mock: Mocker,
        caplog: LogCaptureFixture,
    ) -> None:
        """
        Tests firebase-api-response handling, test 404 response

        :param settings: The Django settings
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
        """
        status = self.send_all_with_mocked_response(
            settings, requests_mock, self.response_mock_data["404"]
        )
        for record in caplog.records:
            assert "Received invalid response from FCM for" in record.message
        assert not status

    @pytest.mark.django_db
    def send_all_with_mocked_response(
        self,
        settings: SettingsWrapper,
        requests_mock: Mocker,
        mocked_response: dict[str, Any],
    ) -> bool:
        """
        Fires a :meth:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient.send_all`
        with mocked post

        :param settings: The Django settings
        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :param mocked_response: Data for the mocked response, depending on test-scenario (given by
                                :attr:`~tests.firebase_api.test_firebase_api_client.TestFirebaseApiClient.response_mock_data`)
        :return: Success status of the notification sending
        """
        status_code = mocked_response.pop("status_code")
        settings.FCM_ENABLED = True
        requests_mock.post(
            settings.FCM_URL, json=mocked_response, status_code=status_code
        )
        notification = PushNotification.objects.first()
        pns = FirebaseApiClient(notification)
        return pns.send_all()

    @pytest.mark.django_db
    def test_region_notification_send(
        self, settings: SettingsWrapper, load_test_data: None, requests_mock: Mocker
    ) -> None:
        targets = set()

        def evaluate_request(request: _RequestObjectProxy, context: _Context) -> object:
            targets.add(request.json()["message"]["topic"])
            return self.response_mock_data["200_success"]

        requests_mock.post(settings.FCM_URL, json=evaluate_request, status_code=200)

        settings.FCM_ENABLED = True

        notification = PushNotification.objects.get(pk=1)

        pns = FirebaseApiClient(notification)
        pns.send_all()

        assert targets == {
            "augsburg-en-news",
            "augsburg-de-news",
        }

    @pytest.mark.django_db
    def test_multiple_regions_notification_send(
        self, settings: SettingsWrapper, load_test_data: None, requests_mock: Mocker
    ) -> None:
        targets = set()

        def evaluate_request(request: _RequestObjectProxy, context: _Context) -> object:
            targets.add(request.json()["message"]["topic"])
            return self.response_mock_data["200_success"]

        requests_mock.post(settings.FCM_URL, json=evaluate_request, status_code=200)

        settings.FCM_ENABLED = True

        notification = PushNotification.objects.get(pk=1)
        notification.regions.add(Region.objects.get(slug="nurnberg"))

        pns = FirebaseApiClient(notification)
        pns.send_all()

        assert targets == {
            "nurnberg-en-news",
            "nurnberg-de-news",
            "augsburg-en-news",
            "augsburg-de-news",
        }
