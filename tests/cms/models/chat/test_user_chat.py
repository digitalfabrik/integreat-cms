from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_django import Settings

import pytest

from integreat_cms.cms.models import UserChat


@pytest.mark.django_db
def test_update_mt_budget(load_test_data: None, settings: Settings) -> None:
    """
    Test if words are being correctly added to the used MT budget and chat word count
    in :meth:`~integreat_cms.cms.models.chat.user_chat.Chat.update_mt_budget`
    """
    # Set custom setting for test
    WORDS_GENERATED = 155
    CUSTOM_BUDGET_WEIGHT = 5
    settings.INTEGREAT_CHAT_BUDGET_WEIGHT = CUSTOM_BUDGET_WEIGHT

    chat = UserChat.objects.get(pk=1)
    mt_budget_before = chat.region.mt_budget_used
    total_words_generated_before = chat.total_words_generated

    chat.update_mt_budget(WORDS_GENERATED)
    assert chat.total_words_generated == WORDS_GENERATED + total_words_generated_before
    assert (
        chat.region.mt_budget_used
        == WORDS_GENERATED * CUSTOM_BUDGET_WEIGHT + mt_budget_before
    )

    # Undo changes to database
    chat.region.mt_budget_used = mt_budget_before
    chat.region.save()
    chat.total_words_generated = total_words_generated_before
    chat.save()
    assert chat.region.mt_budget_used == mt_budget_before
    assert chat.total_words_generated == total_words_generated_before
