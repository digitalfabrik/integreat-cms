from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

import pytest
from django.core.management.base import CommandError
from linkcheck.listeners import enable_listeners
from linkcheck.models import Link, Url

from ..utils import get_command_output


@pytest.mark.django_db
def test_no_argument_fails() -> None:
    """
    Tests that the command fails when no argument is supplied.
    """
    with pytest.raises(CommandError) as exc_info:
        get_command_output("update_link_text")

    assert (
        str(exc_info.value)
        == "Error: the following arguments are required: --target-url, --new-link-text"
    )


@pytest.mark.django_db
def test_no_url_fails() -> None:
    """
    Tests that the command fails when no URL is supplied.
    """
    with pytest.raises(CommandError) as exc_info:
        get_command_output("update_link_text", new_link_text="New Link Text")

    assert (
        str(exc_info.value)
        == "Error: the following arguments are required: --target-url"
    )


@pytest.mark.django_db
def test_no_new_link_text_fails() -> None:
    """
    Tests that the command fails when no link text is supplied.
    """
    with pytest.raises(CommandError) as exc_info:
        get_command_output(
            "update_link_text",
            target_url="https://not-used-in-our-system.nonexistence",
        )

    assert (
        str(exc_info.value)
        == "Error: the following arguments are required: --new-link-text"
    )


NOT_USED_URL = "https://not-used-in-our-system.nonexistence"


@pytest.mark.django_db
def test_fails_if_no_url_found(load_test_data: None) -> None:
    """
    Tests that the command fails when there is no URL object that has the given URL.
    """
    assert not Url.objects.filter(url=NOT_USED_URL).exists()
    with pytest.raises(CommandError) as exc_info:
        get_command_output(
            "update_link_text",
            target_url=NOT_USED_URL,
            new_link_text="New Link Text",
        )

    assert (
        str(exc_info.value) == f'URL object with url "{NOT_USED_URL}" does not exist.'
    )


USED_URL = "https://integreat.app/augsburg/de/willkommen/"
NEW_LINK_TEXT = "New Link Text"
NEW_LINK = f'<a href="{USED_URL}">{NEW_LINK_TEXT}</a>'


@pytest.mark.skip(reason="flaky test having strange side effects")
@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_command_succeeds(load_test_data_transactional: Any | None) -> None:
    """
    Tests that the command runs successfully when supplied with an occurring URL
    and that both the content and indexed link object are updated accordingly.
    """
    target_url = Url.objects.filter(url=USED_URL).first()
    assert target_url
    target_links = Link.objects.filter(url=target_url)
    assert bool(target_links)
    for link in target_links:
        assert link.text != NEW_LINK_TEXT

    number_of_target_links = len(target_links)

    with enable_listeners():
        out, _ = get_command_output(
            "update_link_text", target_url=USED_URL, new_link_text=NEW_LINK_TEXT
        )

    target_url = Url.objects.filter(url=USED_URL).first()
    updated_links = Link.objects.filter(url=target_url)
    assert len(updated_links) == number_of_target_links
    for link in updated_links:
        assert link.text == NEW_LINK_TEXT
        assert NEW_LINK in link.content_object.content

    assert "✔ Successfully finished updating link texts." in out
