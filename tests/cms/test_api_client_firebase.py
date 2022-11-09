import pytest
from django.core.exceptions import ImproperlyConfigured
from integreat_cms.api_client_firebase.push_notification_sender import (
    PushNotificationSender,
)
from integreat_cms.cms.models.push_notifications.push_notification import (
    PushNotification,
)


class TestApiClientFirebase:
    """
    Test for api_client_firebase / push_notification_sender-class (pns)
        
    Firebase Api-Mock-tests (test_firebase_api_?):
    test just correct return (True/False) and logging depending on the firebase-HTTPresponse
    It does not test if firebase-api-server works/answers as expected
    """
    
    # Pushnotification-getter
    @pytest.mark.django_db
    def __get_notification(self):
        """
        :return: a pushNotification (first of test_db-entry)
        :rtype:  pushNotification data model object
        """
        pn_instance = PushNotification.objects.first()
        return pn_instance
    
    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_pns_throws_exeption_when_pns_disabled(self, settings, load_test_data):
        """
        Tests that an ImproperlyConfigured exception is thrown, if pns is disabled in settings   
        
        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple 
        """
        
        settings.FCM_ENABLED = False
        notification = self.__get_notification()
        with pytest.raises(ImproperlyConfigured):
            PushNotificationSender(notification)

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_pns_is_valid(self, settings, load_test_data):
        """
        Tests that PushNotificationSender().is_valid() is true, 
        when FCM_ENABLED and pushNotification valid (with title and translation)   
        
        :param settings: The Django settings
        :type settings: :fixture:`settings`
        
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple 
        
        """
        
        settings.FCM_ENABLED = True
        notification = self.__get_notification()
        assert PushNotificationSender(notification).is_valid()
    
    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_pns_is_not_valid_when_no_translation(self, settings, load_test_data):
        """
        Tests that PushNotificationSender().is_valid() is false, 
        when translation missing   
        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple 
         
        """
        
        settings.FCM_ENABLED = True
        notification = self.__get_notification()
        pns = PushNotificationSender(notification)
        pns.prepared_pnts = []
        assert not pns.is_valid()

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_pns_is_not_valid_when_no_title(self, settings, load_test_data):
        """
        Tests that PushNotificationSender().is_valid() is false, 
        when pushNotification-title is missing  
       
        :param settings: The Django settings
        :type settings: :fixture:`settings`
        
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple 
        """
        
        settings.FCM_ENABLED = True
        notification = self.__get_notification()
        pns = PushNotificationSender(notification)
        pns.prepared_pnts[0].title = ""
        assert not pns.is_valid()


    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_200_success(
        self, settings, load_test_data, requests_mock, caplog
    ):
        """
        Tests firebase-api-response handling, 
        test a successfull api call
           
        :param settings: The Django settings
        :type settings: :fixture:`settings`

        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple 
        
        :param requests_mock: library for mocking requests in pytest
        :type requests_mock: library load by pytest
        
        :param caplog: library for reaching log-entries in test-scenario
        :type caplog: library load by pytest
        """
        
        mockedresponse = self.__get_firebase_response_mock_data("200_success")
        status = self.__send_all_with_mockedresponse(
            settings, requests_mock, mockedresponse
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
        test a partial successfull api call - HTTP 200 but no message_id in response
           
        :param settings: The Django settings
        :type settings: :fixture:`settings`
        
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple 
        
        :param requests_mock: library for mocking requests in pytest
        :type requests_mock: library load by pytest
        
        :param caplog: library for reaching log-entries in test-scenario
        :type caplog: library load by pytest
        """
        
        mockedresponse = self.__get_firebase_response_mock_data("200_no_message_id")
        status = self.__send_all_with_mockedresponse(
            settings, requests_mock, mockedresponse
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
        
        :param requests_mock: library for mocking requests in pytest
        :type requests_mock: library load by pytest
        
        :param caplog: library for reaching log-entries in test-scenario
        :type caplog: library load by pytest
        """
        
        mockedresponse = self.__get_firebase_response_mock_data("401_invalid_key")
        status = self.__send_all_with_mockedresponse(
            settings, requests_mock, mockedresponse
        )
        for record in caplog.records:
            assert "Received invalid response from FCM for" in record.message
        assert not status

    # pylint: disable=unused-argument
    @pytest.mark.django_db
    def test_firebase_api_404(self, settings, load_test_data, requests_mock, caplog):
        """
        Tests firebase-api-response handling, 
        test 404 response
           
        :param settings: The Django settings
        :type settings: :fixture:`settings`
        
        :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
        :type load_test_data: tuple 
        
        :param requests_mock: library for mocking requests in pytest
        :type requests_mock: library load by pytest
        
        :param caplog: library for reaching log-entries in test-scenario
        :type caplog: library load by pytest
        """
        
        mockedresponse = self.__get_firebase_response_mock_data("404")
        status = self.__send_all_with_mockedresponse(
            settings, requests_mock, mockedresponse
        )
        for record in caplog.records:
            assert "Received invalid response from FCM for" in record.message
        assert not status

    #
    # Configure here the mocks for https://fcm.googleapis.com/fcm/send - responses
    #
    def __get_firebase_response_mock_data(self, test_case):
        """
        Helper for configuring different mocked responses  firebase-api-response handling, 
        returns a set of response-data for the mocking-function  
           
        :param test_case: test-title / index for response-data-entry
        :type test_case: string 
        
        :return  resonse_mock_data: set of response-data
        :rtype  response_mock_data: dic
        """
        
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
        """
        fires a PushNotificationSender.send_all() with mocked post
        
        
        :param mockedresponse: data for the mockresponse, depending on test-scenario (given by def __get_firebase_response_mock_data):
        :type mockedresponse: dic
        
        :param settings: The Django settings
        :type settings: :fixture:`settings`
        
        :param requests_mock: library for mocking requests in pytest
        :type requests_mock: library load by pytest

        :return  pns.send_all(): success status of the notification sending
        :rtype  pns.send_all(): boolean
        """
        
        status_code = mockedresponse["status_code"]
        mockedresponse.pop("status_code")
        settings.FCM_ENABLED = True
        requests_mock.post(
            settings.FCM_URL, json=mockedresponse, status_code=status_code
        )
        notification = self.__get_notification()
        pns = PushNotificationSender(notification)
        return pns.send_all()
