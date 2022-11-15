from integreat_cms.cms.utils.translation_utils import translate_link


def test_translate_link():
    """
    Test whether the :meth:`~integreat_cms.cms.utils.translation_utils.translate_link` function correctly escapes message
    text while preserving the link tags
    """
    assert (
        translate_link(
            "<script>alert('dangerous message!')</script>\"<broken>'\" <a>and <asasd>link</a>",
            attributes={
                "href": "=da&nge'rous <link>",
                "class": "<danger>ous '\"class>",
            },
        )
        == "&lt;script&gt;alert(&#x27;dangerous message!&#x27;)&lt;/script&gt;&quot;&lt;broken&gt;&#x27;&quot; <a href="
        "'=da&amp;nge&#x27;rous &lt;link&gt;' class='&lt;danger&gt;ous &#x27;&quot;class&gt;'>and &lt;asasd&gt;link</a>"
    )
