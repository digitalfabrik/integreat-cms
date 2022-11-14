import pytest
from django.core.exceptions import ImproperlyConfigured

from integreat_cms.firebase_api.firebase_api_client import FirebaseApiClient
from integreat_cms.cms.models.push_notifications.push_notification import (
    PushNotification,
)


class TestFirebaseApiClient:
    """
    Test for :class:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient`

    Only tests the correct result (``True``/``False``) and logging output depending on the firebase-HTTP response.
    It does not test if firebase-api-server works/answers as expected.
    """

    #: A set of response-data for the mocking-function
    #: according to https://fcm.googleapis.com/fcm/send
    response_mock_data = {
        "200_success": {"message_id": 1, "reason": "", "status_code": 200},
        "200_no_message_id": {"reason": "", "status_code": 200},
        "401_invalid_key": {"reason": "invalid key", "status_code": 401},
        "404": {"reason": "", "status_code": 404},
    }

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_client_throws_exception_when_fcm_disabled(self, settings, load_test_data):
        """
        Tests that an ImproperlyConfigured exception is thrown, if firebase API is disabled in settings

        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple
        """
        settings.FCM_ENABLED = False
        notification = PushNotification.objects.first()
        with pytest.raises(ImproperlyConfigured):
            FirebaseApiClient(notification)

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_is_valid(self, settings, load_test_data):
        """
        Tests that :meth:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient.is_valid` is ``True``,
        when FCM_ENABLED and pushNotification valid (with title and translation)

        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple
        """
        settings.FCM_ENABLED = True
        notification = PushNotification.objects.first()
        assert FirebaseApiClient(notification).is_valid()

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_is_invalid_when_no_translation(self, settings, load_test_data):
        """
        Tests that :meth:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient.is_valid` is ``False``,
        when translation missing

        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple
        """
        settings.FCM_ENABLED = True
        notification = PushNotification.objects.first()
        pns = FirebaseApiClient(notification)
        pns.prepared_pnts = []
        assert not pns.is_valid()

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_is_invalid_when_no_title(self, settings, load_test_data):
        """
        Tests that :meth:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient.is_valid` is ``False``,
        when pushNotification-title is missing

        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple
        """
        settings.FCM_ENABLED = True
        notification = PushNotification.objects.first()
        pns = FirebaseApiClient(notification)
        pns.prepared_pnts[0].title = ""
        assert not pns.is_valid()

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_200_success(
        self, settings, load_test_data, requests_mock, caplog
    ):
        """
        Tests firebase-api-response handling, test a successful API call

        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple

        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :type requests_mock: ~requests_mock.mocker.Mocker

        :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
        :type caplog: ~_pytest.logging.LogCaptureFixture
        """
        status = self.send_all_with_mocked_response(
            settings, requests_mock, self.response_mock_data["200_success"]
        )
        for record in caplog.records:
            assert "sent, FCM id: 1" in record.message
        assert status

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_200_unexpected_api_response(
        self, settings, load_test_data, requests_mock, caplog
    ):
        """
        Tests firebase-api-response handling,
        test a partial successful api call - HTTP 200 but no message_id in response

        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple

        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :type requests_mock: ~requests_mock.mocker.Mocker

        :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
        :type caplog: ~_pytest.logging.LogCaptureFixture
        """
        status = self.send_all_with_mocked_response(
            settings, requests_mock, self.response_mock_data["200_no_message_id"]
        )
        for record in caplog.records:
            assert "sent, but unexpected API response" in record.message
        assert status

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_403_wrong_token(
        self, settings, load_test_data, requests_mock, caplog
    ):
        """
        Tests firebase-api-response handling,
        test a denied call - HTTP 403 because of wrong auth-token

        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple

        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :type requests_mock: ~requests_mock.mocker.Mocker

        :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
        :type caplog: ~_pytest.logging.LogCaptureFixture
        """
        status = self.send_all_with_mocked_response(
            settings, requests_mock, self.response_mock_data["401_invalid_key"]
        )
        for record in caplog.records:
            assert "Received invalid response from FCM for" in record.message
        assert not status

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_404(self, settings, load_test_data, requests_mock, caplog):
        """
        Tests firebase-api-response handling, test 404 response

        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple

        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :type requests_mock: ~requests_mock.mocker.Mocker

        :param caplog: Fixture for asserting log messages in tests (see :fixture:`pytest:caplog`)
        :type caplog: ~_pytest.logging.LogCaptureFixture
        """
        status = self.send_all_with_mocked_response(
            settings, requests_mock, self.response_mock_data["404"]
        )
        for record in caplog.records:
            assert "Received invalid response from FCM for" in record.message
        assert not status

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def send_all_with_mocked_response(self, settings, requests_mock, mocked_response):
        """
        Fires a :meth:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient.send_all`
        with mocked post

        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param requests_mock: Fixture for mocking requests, see :doc:`requests-mock:pytest`
        :type requests_mock: ~_pytest.logging.LogCaptureFixture

        :param mocked_response: Data for the mocked response, depending on test-scenario (given by
                                :attr:`~tests.firebase_api.test_firebase_api_client.TestFirebaseApiClient.response_mock_data`)
        :type mocked_response: dict

        :return: Success status of the notification sending
        :rtype: bool
        """
        status_code = mocked_response.pop("status_code")
        settings.FCM_ENABLED = True
        requests_mock.post(
            settings.FCM_URL, json=mocked_response, status_code=status_code
        )
        notification = PushNotification.objects.first()
        pns = FirebaseApiClient(notification)
        return pns.send_all()
