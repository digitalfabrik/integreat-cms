from __future__ import annotations

import pytest

from integreat_cms.cms.utils.text_utils import strip_html_with_whitespace


@pytest.mark.parametrize(
    "content,expected",
    [
        ("Welcome<br>to Augsburg", "Welcome to Augsburg"),
        ("<p>Welcome</p><p>to Augsburg</p>", "Welcome to Augsburg"),
        ("<div>Welcome</div><ul><li>to</li><li>Augsburg</li></ul>", "Welcome to Augsburg"),
        ("Welcome <a href=\"/more\">to Augsburg</a>", "Welcome to Augsburg"),
    ],
)
def test_strip_html_with_whitespace(content: str, expected: str) -> None:
    """Structural HTML should not concatenate neighboring words in an excerpt."""
    assert strip_html_with_whitespace(content) == expected
