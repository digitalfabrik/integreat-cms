import pytest
from integreat_cms.api_client_firebase.push_notification_sender import PushNotificationSender
from integreat_cms.cms.models.push_notifications.push_notification import PushNotification
from django.core.exceptions import ImproperlyConfigured

#######################################################################
# Test for api_client_firebase / push_notification_sender-class (pns) 
# @TODO
# def test_pns_send_pn()
# def test_pns_send_all()
#######################################################################
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