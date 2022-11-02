import pytest
from integreat_cms.api_client_firebase.push_notification_sender import PushNotificationSender
from integreat_cms.cms.models.push_notifications.push_notification import PushNotification
from integreat_cms.cms.constants.push_notifications import ONLY_AVAILABLE
from django.core.exceptions import ImproperlyConfigured

class TestApiClientFirebase:
    def __get_notification(self, settings):
        pn_instance = PushNotification.objects.first()
        return pn_instance

    @pytest.mark.django_db
    def test_pns_throws_exeption_when_pns_disabled(self, settings, load_test_data):
        settings.FCM_ENABLED = False
        notification = self.__get_notification(settings)
        with pytest.raises(ImproperlyConfigured):
            PushNotificationSender(notification)
        
    @pytest.mark.django_db
    def test_pns_is_valid(self, settings, load_test_data):
        settings.FCM_ENABLED = True
        notification = self.__get_notification(settings)
        assert PushNotificationSender(notification).is_valid()

    @pytest.mark.django_db
    def test_pns_is_not_valid_when_no_translation(self, settings, load_test_data):
        settings.FCM_ENABLED = True
        notification = self.__get_notification(settings)
        pns = PushNotificationSender(notification)
        pns.prepared_pnts = []
        assert pns.is_valid() == False

    @pytest.mark.django_db
    def test_pns_is_not_valid_when_no_title(self, settings, load_test_data):
        settings.FCM_ENABLED = True
        notification = self.__get_notification(settings)
        pns = PushNotificationSender(notification)
        pns.prepared_pnts[0].title = ""
        assert pns.is_valid() == False
    

    # to test the function firestore local emulator should be used: 
    # how to initialize it? 
    @pytest.mark.django_db
    def test_pns_send_pn(self, settings):
        # self.__start_firebase_emulator()
        settings.FCM_ENABLED = True
        settings.FCM_KEY = 'firebase_emulater_key'
        pns = PushNotificationSender(self.__get_notification)
        pns.fcm_url = 'firebase_emulator_url/localhost:port'
    #   pns.send_pn()
    #   local_firebase_notification = self.__get_notification_from_firebase_emulator()

    #     settings.FCM_ENABLED = True
    #     notification = self.__get_notification(settings)
    #     pns = PushNotificationSender(notification)
    #     pnt = pns.prepared_pnts[0]
    #     requestValue = pns.send_pn(pnt)
        assert 0 == 1
    
    @pytest.mark.django_db
    def test_pns_send_all(self, settings):
        assert 0 == 1    

    #@todo: rename all api-clients to api_client_name





 



     



        