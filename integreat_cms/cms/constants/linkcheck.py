from django.utils.translation import gettext_lazy as _

LINKCHECK_STATUS_TRANSLATIONS = [
    _(
        "New Connection Error: Failed to establish a new connection: "
        "[Errno -2] Name or service not known"
    ),
    _("SSL Error: wrong version number"),
    _("The read operation timed out"),
    _(
        "Connection Error: ('Connection aborted.', "
        "ConnectionResetError(104, 'Connection reset by peer'))"
    ),
]

LINK_TYPES = [
    ("internal", _("Internal links")),
    ("external", _("External links")),
    ("mailto", _("Email links")),
    ("phone", _("Phone links")),
    ("invalid", _("Invalid links")),
]
