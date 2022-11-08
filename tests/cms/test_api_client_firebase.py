import pytest
from integreat_cms.api_client_firebase.push_notification_sender import (
    PushNotificationSender,
)
from integreat_cms.cms.models.push_notifications.push_notification import (
    PushNotification,
)
from django.core.exceptions import ImproperlyConfigured

#######################################################################
# Test for api_client_firebase / push_notification_sender-class (pns)
#######################################################################
class TestApiClientFirebase:

    # Pushnotification-getter
    @pytest.mark.django_db
    def __get_notification(self):
        pn_instance = PushNotification.objects.first()
        return pn_instance
    
    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_pns_throws_exeption_when_pns_disabled(self, settings, load_test_data):
        settings.FCM_ENABLED = False
        notification = self.__get_notification()
        with pytest.raises(ImproperlyConfigured):
            PushNotificationSender(notification)

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_pns_is_valid(self, settings, load_test_data):
        settings.FCM_ENABLED = True
        notification = self.__get_notification()
        assert PushNotificationSender(notification).is_valid()
    
    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_pns_is_not_valid_when_no_translation(self, settings, load_test_data):
        settings.FCM_ENABLED = True
        notification = self.__get_notification()
        pns = PushNotificationSender(notification)
        pns.prepared_pnts = []
        assert pns.is_valid() == False

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_pns_is_not_valid_when_no_title(self, settings, load_test_data):
        settings.FCM_ENABLED = True
        notification = self.__get_notification()
        pns = PushNotificationSender(notification)
        pns.prepared_pnts[0].title = ""
        assert pns.is_valid() == False

    #
    # Firebase Api-Mock-Test:
    # tests just correct return (True/False) and logging depending on the firebase-HTTPresponse
    # It does not test if firebase-api-server works/answers as expected
    #
    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_200_success(
        self, settings, load_test_data, requests_mock, caplog
    ):
        mockedresponse = self.__get_firebase_response_mock_data("200_success")
        status = self.__send_all_with_mockedresponse(
            settings, requests_mock, mockedresponse
        )
        for record in caplog.records:
            assert "sent, FCM id: 1" in record.message
        assert True == status

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_200_unexpected_api_response(
        self, settings, load_test_data, requests_mock, caplog
    ):
        mockedresponse = self.__get_firebase_response_mock_data("200_no_message_id")
        status = self.__send_all_with_mockedresponse(
            settings, requests_mock, mockedresponse
        )
        for record in caplog.records:
            assert "sent, but unexpected API response" in record.message
        assert True == status

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_403_wrong_token(
        self, settings, load_test_data, requests_mock, caplog
    ):
        mockedresponse = self.__get_firebase_response_mock_data("401_invalid_key")
        status = self.__send_all_with_mockedresponse(
            settings, requests_mock, mockedresponse
        )
        for record in caplog.records:
            assert "Received invalid response from FCM for" in record.message
        assert False == status

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_404(self, settings, load_test_data, requests_mock, caplog):
        mockedresponse = self.__get_firebase_response_mock_data("404")
        status = self.__send_all_with_mockedresponse(
            settings, requests_mock, mockedresponse
        )
        for record in caplog.records:
            assert "Received invalid response from FCM for" in record.message
        assert False == status

    #
    # Configure here the mocks for https://fcm.googleapis.com/fcm/send - responses
    #
    def __get_firebase_response_mock_data(self, test_case):
        resonse_mock_data = {
            "200_success": {"message_id": 1, "reason": "", "status_code": 200},
            "200_no_message_id": {"reason": "", "status_code": 200},
            "401_invalid_key": {"reason": "invalid key", "status_code": 401},
            "404": {"reason": "", "status_code": 404},
        }
        return resonse_mock_data[test_case]

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def __send_all_with_mockedresponse(self, settings, requests_mock, mockedresponse):
        status_code = mockedresponse["status_code"]
        mockedresponse.pop("status_code")
        settings.FCM_ENABLED = True
        requests_mock.post(
            settings.FCM_URL, json=mockedresponse, status_code=status_code
        )
        notification = self.__get_notification()
        pns = PushNotificationSender(notification)
        return pns.send_all()
