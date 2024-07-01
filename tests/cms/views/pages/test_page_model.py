import pytest
from django.test.client import Client
from django.urls import resolve, reverse

from integreat_cms.cms.models.pages.page_translation import PageTranslation
from tests.conftest import EDITOR, MANAGEMENT, PRIV_STAFF_ROLES


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.django_db
def test_clean_content(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "PUBLIC",
            "content": '<h1>Das ist eine H1</h1><pre>Das ist vordefinierter Text</pre><code>Das ist vordefinierter Code</code><a href="https://www.integreat-app.de"></a><a href="http://localhost:8000/augsburg/pages/de/5" class="link-external"></a>',
            "title": "Autosave Page",
            "slug": "autosave-page",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": True,
        },
    )

    assert response.status_code == 302
    edit_page_url = response.headers.get("location")
    id_of_page = resolve(edit_page_url).kwargs["page_id"]

    translation = PageTranslation.objects.get(page__id=id_of_page)

    # Test convert_heading works
    assert "<h1>Das ist eine H1</h1>" not in translation.content
    assert "<h2>Das ist eine H1</h2>" in translation.content

    # Test convert_monospaced_tags works
    assert "<pre>Das ist vordefinierter Text</pre>" not in translation.content
    assert "<code>Das ist vordefinierter Code</code>" not in translation.content
    assert "<p>Das ist vordefinierter Text</p>" in translation.content
    assert "<p>Das ist vordefinierter Code</p>" in translation.content

    # Test update_links works
    assert (
        'a href="https://www.integreat-app.de" class="link-external"'
        in translation.content
    )
    assert (
        '<a href="http://localhost:8000/augsburg/pages/de/5" class="link-external">'
        not in translation.content
    )
    assert (
        '<a href="http://localhost:8000/augsburg/pages/de/5"></a>'
        in translation.content
    )
