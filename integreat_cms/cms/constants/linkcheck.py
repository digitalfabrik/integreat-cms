from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final


LINKCHECK_STATUS_TRANSLATIONS: Final = [
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

LINK_TYPES: Final = [
    ("internal", _("Internal links")),
    ("external", _("External links")),
    ("mailto", _("Email links")),
    ("phone", _("Phone links")),
    ("invalid", _("Invalid links")),
]
