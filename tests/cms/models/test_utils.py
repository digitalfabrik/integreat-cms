from types import SimpleNamespace

from django.utils.safestring import mark_safe

from integreat_cms.cms.models.utils import format_object_translation


def test_format_object_translation_decodes_escaped_plain_title() -> None:
    translation = SimpleNamespace(
        language=SimpleNamespace(slug="en"),
        link_title=mark_safe("&quot;Welcome&quot;"),
        path=lambda: "pages/welcome",
        get_absolute_url=lambda: "/en/welcome/",
    )

    result = format_object_translation(translation, "page", "en")

    assert result["title"] == '"Welcome"'
    assert result["html_title"] == "&quot;Welcome&quot;"
