import pytest
from django.conf import settings

from integreat_cms.cms.models import UserChat


@pytest.mark.django_db
def test_update_mt_budget() -> None:
    """
    Test if words are being correctly added to the used MT budget and chat word count
    """
    chat = UserChat.objects.get(pk=1)
    mt_budget_before = chat.region.mt_budget_used
    total_words_generated_before = chat.total_words_generated
    words_generated = 155
    chat.update_mt_budget(words_generated)
    assert chat.total_words_generated == words_generated + total_words_generated_before
    assert (
        chat.region.mt_budget_used
        == words_generated * settings.INTEGREAT_CHAT_BUDGET_WEIGHT + mt_budget_before
    )

    # Undo changes to database
    chat.region.mt_budget_used = mt_budget_before
    chat.region.save()
    chat.total_words_generated = total_words_generated_before
    chat.save()
    assert chat.region.mt_budget_used == mt_budget_before
    assert chat.total_words_generated == total_words_generated_before
