TEXTLAB_NORMALIZE_TEXT = [
    (
        "<p>One paragraph</p>",
        "<p>One paragraph</p>",
    ),
    (
        "<p><strong>One</strong> paragraph</p>",
        "<p><strong>One</strong> paragraph</p>",
    ),
    (
        "<p><strong>One</strong> paragraph</p><p>&nbsp;&nbsp;</p><p>&nbsp;</p>",
        "<p><strong>One</strong> paragraph</p>",
    ),
    (
        "<div><p>One paragraph</p></div>",
        "<p>One paragraph</p>",
    ),
    (
        "<div><p>One paragraph</p><p>&nbsp;&nbsp;</p><p>&nbsp;</p></div>",
        "<p>One paragraph</p>",
    ),
    (
        "<h2>Some header</h2>",
        "<h2>Some header</h2>",
    ),
    (
        "<h2>Some header</h2><h2>&nbsp;&nbsp;</h2><h2>&nbsp;</h2>",
        "<h2>Some header</h2>",
    ),
    (
        "<h2>Some header</h2><p>&nbsp;&nbsp;</p>",
        "<h2>Some header</h2>",
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
        '<div>\n<p><a href="some.url">Some link</a></p></div>',
        '<p><a href="some.url">Some link</a></p>',
    ),
    (
        '<div><p>Some image</p><p><a href="some.image"><img src="some.image" alt=""></a></p><p>&nbsp;</p></div>',
        "<p>Some image</p>",
    ),
    (
        '<p><a href="some.image"><img src="some.image" alt=""></a></p>',
        "<p></p>",
    ),
    (
        '<div><p>Some video</p><p><video controls="controls" width="300" height="150"><source src="some.video" /></video></p></div>',
        "<p>Some video</p>",
    ),
    (
        '<p><video controls="controls" width="300" height="150"><source src="some.video" /></video></p>',
        "<p></p>",
    ),
]
