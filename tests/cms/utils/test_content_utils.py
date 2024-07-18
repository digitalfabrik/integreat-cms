import pytest
from django.test.client import Client

from integreat_cms.cms.utils.content_utils import clean_content
from tests.conftest import EDITOR, MANAGEMENT, PRIV_STAFF_ROLES


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.django_db
def test_clean_content(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    raw_content = '<h1>Das ist eine H1</h1><pre>Das ist vordefinierter Text</pre><code>Das ist vordefinierter Code</code><a href="https://www.integreat-app.de"></a><a href="http://localhost:8000/augsburg/pages/de/5" class="link-external"></a>'
    cleaned_content = clean_content(raw_content, "de")

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
