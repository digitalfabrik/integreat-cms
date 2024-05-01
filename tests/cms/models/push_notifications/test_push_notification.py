import pytest
from django.utils import translation

from integreat_cms.cms.models import (
    Language,
    PushNotification,
    PushNotificationTranslation,
)


@pytest.mark.django_db
def test_best_translation(load_test_data: None) -> None:
    """
    Test whether the `best_translation` method functions correctly. This is to prevent the following bug: https://github.com/digitalfabrik/integreat-cms/issues/2726
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    pn = PushNotification.objects.get(translations__title="Test")

    with translation.override("de"):
        assert pn.best_translation.title == "Test"

    with translation.override("en"):
        # This push notification has no other translations than the German one and should thus always return
        # the German translation as the best translation
        assert pn.best_translation.title == "Test"

    PushNotificationTranslation.objects.filter(
        push_notification=pn, language__slug="en"
    ).update(title="English test")
    with translation.override("en"):
        assert pn.best_translation.title == "English test"
