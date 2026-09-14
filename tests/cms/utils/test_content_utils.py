import pytest
from django.test.client import Client
from django.utils import translation
from lxml.html import tostring

from integreat_cms.cms.utils.content_utils import clean_content, render_contact_card
from tests.constants import EDITOR, MANAGEMENT, PRIV_STAFF_ROLES


@pytest.mark.parametrize(
    "login_role_user",
    [*PRIV_STAFF_ROLES, MANAGEMENT, EDITOR],
    indirect=True,
)
@pytest.mark.django_db
def test_clean_content(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    raw_content = '<h1>Das ist eine H1</h1><pre>Das ist vordefinierter Text</pre><code>Das ist vordefinierter Code</code><a href="https://www.integreat-app.de"></a><a href="http://localhost:8000/augsburg/pages/de/5" class="link-external"></a>'
    cleaned_content = clean_content(raw_content, "de", 1)

    # Test convert_heading works
    assert "<h1>Das ist eine H1</h1>" not in cleaned_content
    assert "<h2>Das ist eine H1</h2>" in cleaned_content

    # Test convert_monospaced_tags works
    assert "<pre>Das ist vordefinierter Text</pre>" not in cleaned_content
    assert "<code>Das ist vordefinierter Code</code>" not in cleaned_content
    assert "<p>Das ist vordefinierter Text</p>" in cleaned_content
    assert "<p>Das ist vordefinierter Code</p>" in cleaned_content

    # Test update_links works
    assert (
        'a href="https://www.integreat-app.de" class="link-external"' in cleaned_content
    )
    assert (
        '<a href="http://localhost:8000/augsburg/pages/de/5" class="link-external">'
        not in cleaned_content
    )
    assert '<a href="http://localhost:8000/augsburg/pages/de/5"></a>' in cleaned_content


def test_clean_content_strips_script_tag() -> None:
    result = clean_content("<p>Hello <script>alert('XSS')</script> world</p>", "de")
    assert "<script>" not in result
    assert "alert(" not in result


def test_clean_content_strips_event_handler() -> None:
    result = clean_content("<p><a onclick='alert(1)'>click me</a></p>", "de")
    assert "onclick" not in result


@pytest.mark.django_db
def test_render_contact_card_same_region(load_test_data: None) -> None:
    """
    Test that render_contact_card renders the contact card when region matches
    """
    # Contact 3 belongs to region 1 (augsburg)
    result = tostring(render_contact_card(3, ["name"], region_id=1), encoding="unicode")
    assert "Mariana Musterfrau" in result


@pytest.mark.django_db
def test_render_contact_card_cross_region(load_test_data: None) -> None:
    """
    Test that render_contact_card returns None when the contact belongs to a different region
    """
    # Contact 3 belongs to region 1 (augsburg), not region 8 (berlin)
    message = "This contact belongs to a different region and cannot be displayed."
    with translation.override("en"):
        assert message in tostring(
            render_contact_card(3, ["name"], region_id=8)
        ).decode("utf-8")
