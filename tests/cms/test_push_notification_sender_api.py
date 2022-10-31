import pytest
from integreat_cms.push_notification_sender_api.push_notification_sender import PushNotificationSenderApi


def test_pns_is_valid():
    pn = PushNotificationSenderApi(helper_get_push_notification())
    print(pn.is_valid())
    assert pn.is_valid() == True

def test_psn_send_all():
    return False

def test_pns_send_pn():
    return False

def helper_get_push_notification():
    return "just a testmessage"

