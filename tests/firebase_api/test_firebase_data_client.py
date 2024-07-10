from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from integreat_cms.firebase_api.firebase_data_client import FirebaseDataClient
from integreat_cms.firebase_api.firebase_security_service import FirebaseSecurityService

if TYPE_CHECKING:
    from typing import Any

    from pytest_django.fixtures import SettingsWrapper
    from requests_mock.mocker import Mocker


class TestFirebaseDataClient:
    """
    Test for :class:`~integreat_cms.firebase_api.firebase_api_client.FirebaseDataClient`
    """

    endpoint_mock_url = "https://fcmdata.googleapis.com/v1beta1/projects/integreat/androidApps/123456/deliveryData"

    response_mock_data = {
        "androidDeliveryData": [
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 5},
                "analyticsLabel": "augsburg",
                "data": {
                    "countMessagesAccepted": "230",
                    "countNotificationsAccepted": "204",
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 5},
                "analyticsLabel": "berlin",
                "data": {
                    "countMessagesAccepted": "430",
                    "countNotificationsAccepted": "305",
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 4},
                "analyticsLabel": "augsburg",
                "data": {
                    "countMessagesAccepted": "628",
                    "countNotificationsAccepted": "493",
                    "proxyNotificationInsightPercents": {"skippedUnsupported": 56},
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 4},
                "analyticsLabel": "berlin",
                "data": {
                    "countMessagesAccepted": "902",
                    "countNotificationsAccepted": "623",
                    "proxyNotificationInsightPercents": {"skippedUnsupported": 55},
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "analyticsLabel": "augsburg",
                "date": {"year": 2024, "month": 7, "day": 3},
                "data": {
                    "countMessagesAccepted": "705",
                    "countNotificationsAccepted": "535",
                    "proxyNotificationInsightPercents": {"skippedUnsupported": 56},
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "analyticsLabel": "berlin",
                "date": {"year": 2024, "month": 7, "day": 3},
                "data": {
                    "countMessagesAccepted": "800",
                    "countNotificationsAccepted": "32",
                    "proxyNotificationInsightPercents": {"skippedUnsupported": 12},
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 2},
                "analyticsLabel": "augsburg",
                "data": {},
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 2},
                "analyticsLabel": "berlin",
                "data": {},
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 1},
                "analyticsLabel": "augsburg",
                "data": {
                    "countMessagesAccepted": "627",
                    "countNotificationsAccepted": "474",
                    "proxyNotificationInsightPercents": {"skippedUnsupported": 73},
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 1},
                "analyticsLabel": "berlin",
                "data": {
                    "countMessagesAccepted": "822",
                    "countNotificationsAccepted": "512",
                    "proxyNotificationInsightPercents": {"skippedUnsupported": 12},
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 6, "day": 30},
                "analyticsLabel": "augsburg",
                "data": {},
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 6, "day": 30},
                "analyticsLabel": "berlin",
                "data": {},
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 6, "day": 29},
                "analyticsLabel": "augsburg",
                "data": {},
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 6, "day": 29},
                "analyticsLabel": "berlin",
                "data": {},
            },
        ]
    }

    unlabeled_response_mock_data = {
        "androidDeliveryData": [
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 5},
                "data": {
                    "countMessagesAccepted": "230",
                    "countNotificationsAccepted": "204",
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 4},
                "data": {
                    "countMessagesAccepted": "628",
                    "countNotificationsAccepted": "493",
                    "proxyNotificationInsightPercents": {"skippedUnsupported": 56},
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 3},
                "data": {
                    "countMessagesAccepted": "705",
                    "countNotificationsAccepted": "535",
                    "proxyNotificationInsightPercents": {"skippedUnsupported": 56},
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 2},
                "data": {},
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 7, "day": 1},
                "data": {
                    "countMessagesAccepted": "627",
                    "countNotificationsAccepted": "474",
                    "proxyNotificationInsightPercents": {"skippedUnsupported": 73},
                },
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 6, "day": 30},
                "data": {},
            },
            {
                "appId": "1:164298278764:android:3fc1f67f3883df306fd549",
                "date": {"year": 2024, "month": 6, "day": 29},
                "data": {},
            },
        ]
    }

    patch: Any = None

    def setup_method(self) -> None:
        self.patch = patch.object(
            FirebaseSecurityService,
            "get_data_access_token",
            return_value="secret access token",
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

        with pytest.raises(ImproperlyConfigured):
            FirebaseDataClient()

    @pytest.mark.django_db
    def test_avg_per_region(
        self, settings: SettingsWrapper, load_test_data: None, requests_mock: Mocker
    ) -> None:
        settings.FCM_DATA_URL = self.endpoint_mock_url
        settings.FCM_ENABLED = True

        requests_mock.get(
            self.endpoint_mock_url,
            json=lambda request, context: self.response_mock_data,
            status_code=200,
        )

        client = FirebaseDataClient()
        response = client.get_notification_statistics_per_region()

        assert response == {
            "augsburg": 426.5,
            "berlin": 368.0,
        }

    @pytest.mark.django_db
    def test_without_analytics_labels(
        self, settings: SettingsWrapper, load_test_data: None, requests_mock: Mocker
    ) -> None:
        settings.FCM_DATA_URL = self.endpoint_mock_url
        settings.FCM_ENABLED = True

        requests_mock.get(
            self.endpoint_mock_url,
            json=lambda request, context: self.unlabeled_response_mock_data,
            status_code=200,
        )

        client = FirebaseDataClient()
        response = client.get_notification_statistics_per_region()

        assert response == {}

    @pytest.mark.django_db
    def test_cache_hit(
        self, settings: SettingsWrapper, load_test_data: None, requests_mock: Mocker
    ) -> None:
        settings.FCM_DATA_URL = self.endpoint_mock_url
        settings.FCM_ENABLED = True

        requests_mock.get(
            self.endpoint_mock_url,
            json=lambda request, context: self.unlabeled_response_mock_data,
            status_code=200,
        )

        client = FirebaseDataClient()

        client.get_notification_statistics_per_region()
        client.get_notification_statistics_per_region()

        assert requests_mock.call_count == 1
