TEXTLAB_NORMALIZE_TEXT = [
    (
        "<p>One paragraph</p>",
        "<div><p>One paragraph</p></div>",
    ),
    (
        "<p>One paragraph</p><p>&nbsp;&nbsp;</p><p>&nbsp;</p>",
        "<div><p>One paragraph</p></div>",
    ),
    (
        "<div><p>One paragraph</p></div>",
        "<div><p>One paragraph</p></div>",
    ),
    (
        "<div><p>One paragraph</p><p>&nbsp;&nbsp;</p><p>&nbsp;</p></div>",
        "<div><p>One paragraph</p></div>",
    ),
    (
        "<p>One paragraph</p><p>Another paragraph</p>",
        "<div>\r\n<p>One paragraph</p>\r\n<p>Another paragraph</p>\r\n</div>",
    ),
    (
        "<div><p>One paragraph</p><p>Another paragraph</p></div>",
        "<div>\r\n<p>One paragraph</p>\r\n<p>Another paragraph</p>\r\n</div>",
    ),
    (
        "<p>One paragraph</p><p>Another paragraph</p><p>&nbsp;&nbsp;</p><p>&nbsp;</p>",
        "<div>\r\n<p>One paragraph</p>\r\n<p>Another paragraph</p>\r\n</div>",
    ),
    (
        "<div><p>One paragraph</p><p>Another paragraph</p><p>&nbsp;&nbsp;</p><p>&nbsp;</p></div>",
        "<div>\r\n<p>One paragraph</p>\r\n<p>Another paragraph</p>\r\n</div>",
    ),
    (
        "<div>\n<p>One paragraph</p>\n<p>Another paragraph</p>\n</div>",
        "<div>\r\n<p>One paragraph</p>\r\n<p>Another paragraph</p>\r\n</div>",
    ),
    (
        "<div>\n<p></p></div>",
        "<div>\r\n</div>",
    ),
    (
        '<div>\n<p><a href="some.url">A link</a></p></div>',
        '<div>\r\n<p><a href="some.url">A link</a></p>\r\n</div>',
    ),
    (
        '<div><p>An image:</p><p><a href="some.image"><img src="some.image" alt=""></a></p></div>',
        '<div>\r\n<p>An image:</p>\r\n<p><a href="some.image"><img src="some.image" alt=""></a></p>\r\n</div>',
    ),
]
