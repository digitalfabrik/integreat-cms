from enum import Enum

from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _


class LinkCheckError:
    value: tuple[Promise, Promise]

    @property
    def error_message(self) -> Promise:
        return self.value[0]

    @property
    def help_text(self) -> Promise:
        return self.value[1]


class ExternalLinkError(LinkCheckError, Enum):
    NOT_FOUND = (
        _("This link no longer exists. Users end up in a dead end."),
        _(
            "Look for a new, matching link on the provider's website "
            "and update the link here.",
        ),
    )
    FORBIDDEN = (
        _(
            "Automatic checking of this link is unfortunately blocked. The system cannot determine whether it is valid or not."
        ),
        _(
            "Click the link. If it works for you, mark it as valid. If not, find a new link or remove the old one."
        ),
    )
    SERVER_ERROR = (
        _("The link cannot be reached (at the moment). Users cannot proceed."),
        _(
            "This error is on the website provider's side and may be temporary. Click the link: if it works, mark it as valid."
        ),
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
        _("This link could not be checked. It may be invalid."),
        _(
            "Click the link. If it works and makes sense, mark it as valid. If not, "
            "look for a valid link and update the link here.",
        ),
    )


class InternalLinkError(LinkCheckError, Enum):
    LINK_TARGET_ARCHIVED = (
        _("The link leads to archived content. Users end up on an error page."),
        _("Use a link to a matching page that is not archived."),
    )
    LINK_TARGET_NOT_PUBLIC = (
        _(
            "The link leads to content that is currently not published. Users end up on an error page."
        ),
        _("Publish this page so users can see the content, or remove the link."),
    )
    #: This error should no longer be possible once we have introduced shortcodes for internal links
    LINK_TARGET_URL_OUTDATED = (
        _("The URL is not up-to-date."),
        _("Look for the matching content again and update the link."),
    )
    LINK_TARGET_NOT_FOUND = (
        _(
            "The linked content could not be found. It may have been deleted or renamed. Users are redirected to an error page."
        ),
        _("Look for the matching content and update the link."),
    )
    LINK_TARGET_PARENT_NOT_PUBLIC = (
        _(
            "The linked page is currently unavailable because its parent page is not published. Users are redirected to an error page."
        ),
        _("Publish the parent page of this link."),
    )
    LINK_TARGET_AMBIGUOUS = (
        _(
            "The link leads to multiple possible pieces of content. The system cannot determine unambiguously which one is meant. Users may see an error.",
        ),
        _("Look for the matching content and update the link."),
    )
    REGION_OR_LANGUAGE_INVALID = (
        _(
            "The linked region or language no longer exists or is not "
            "active. Users end up in a dead end.",
        ),
        _(
            "Check whether the region or language still exists and is "
            "active. Update the link accordingly or remove it.",
        ),
    )
    IMPRINT_MISSING = (
        _("The linked imprint does not exist or is not published in this language."),
        _("Publish the imprint in this language or remove the link."),
    )
    EVENT_OR_LOCATION_INVALID = (
        _("The link to this event or location is malformed."),
        _(
            "Create the link again using the linking feature, instead of "
            "typing the URL by hand.",
        ),
    )
    NEWS_SUBCATEGORY_MISSING = (
        _("This news link does not contain a valid subcategory."),
        _("Create the link again using the linking feature for news."),
    )
    TU_NEWS_DISABLED = (
        _("tü-news is not enabled for this region. The link leads nowhere."),
        _("Enable tü-news for this region or remove the link."),
    )
    NEWS_ENTRY_MISSING = (
        _(
            "This news entry does not exist or has not yet been sent. "
            "Users end up in a dead end.",
        ),
        _(
            "Publish the news entry, or link to a different, already sent news entry.",
        ),
    )
    NEWS_SUBCATEGORY_INVALID = (
        _("The subcategory of this news entry does not exist."),
        _("Create the link again using the linking feature for news."),
    )
    NEWS_URL_INVALID = (
        _("This news link is malformed."),
        _(
            "Create the link again using the linking feature, instead of "
            "typing the URL by hand.",
        ),
    )
    OFFERS_DISABLED = (
        _("Offers are not enabled for this region. The link leads nowhere."),
        _("Enable offers for this region or remove the link."),
    )
    OFFERS_NOT_FOUND = (
        _("This offer no longer exists in this region."),
        _("Look for the matching offer again and update the link."),
    )
    OFFERS_URL_INVALID = (
        _("The link to this offer is malformed."),
        _(
            "Create the link again using the linking feature, instead of "
            "typing the URL by hand.",
        ),
    )

    @property
    def error_code(self) -> str:
        return self.name
