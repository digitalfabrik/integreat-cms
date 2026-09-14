from enum import Enum

from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _


class ExternalLinkError(Enum):
    NOT_FOUND = (
        _("This link no longer exists. Users end up in a dead end."),
        _(
            "Look for a new, matching link on the provider's website "
            "and update the link here.",
        ),
    )

    FORBIDDEN = (
        _("Automatic checking of this link is unfortunately blocked."),
        _("Click the link. If it works for you, mark it as valid."),
    )

    SERVER_ERROR = (
        _("This link cannot (currently) be reached. Users cannot continue."),
        _("This error lies with the website's provider and may be temporary."),
    )

    SSL_INVALID = (
        _(
            "The security certificate of the target page is invalid or "
            "expired. Browsers may warn users before showing the page.",
        ),
        _(
            "Click the link. If a security warning appears, contact the "
            "page's provider or look for an alternative.",
        ),
    )

    UNKNOWN_ERROR = (
        _(
            "This link could not be checked. It may be invalid.",
        ),
        _(
            "Click the link. If it works and makes sense, mark it as valid. If not, "
            "look for a valid link and update the link here.",
        ),
    )

    @property
    def error_message(self) -> Promise:
        return self.value[0]

    @property
    def help_text(self) -> Promise:
        return self.value[1]
