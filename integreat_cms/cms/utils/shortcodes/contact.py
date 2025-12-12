from typing import Any

from lxml.html import tostring

from ..content_utils import render_contact_card
from .utils import shortcode


@shortcode
def contact(
    pargs: list[str],
    kwargs: dict[str, str],  # noqa: ARG001
    context: dict[str, Any] | None,  # noqa: ARG001
    content: str = "",  # noqa: ARG001
) -> str:
    """
    Shortcode to insert a contact card with details from a :class:`~integreat_cms.cms.models.contact.contact.Contact`.

    Positional arguments:

    * ``contact_id`` – The id of the :class:`~integreat_cms.cms.models.contact.contact.Contact` whose details should be displayed

    The remaining positional arguments might be of the following:

    * ``address``             (optional) – Whether the address             should be shown and other, not explicitly wanted details should be hidden
    * ``email``               (optional) – Whether the email address       should be shown and other, not explicitly wanted details should be hidden
    * ``phone_number``        (optional) – Whether the phone number        should be shown and other, not explicitly wanted details should be hidden
    * ``mobile_phone_number`` (optional) – Whether the mobile phone number should be shown and other, not explicitly wanted details should be hidden
    * ``website``             (optional) – Whether the website             should be shown and other, not explicitly wanted details should be hidden
    """
    contact_id = pargs[0] if pargs else None
    options = (
        "address",
        "email",
        "phone_number",
        "mobile_phone_number",
        "website",
    )
    wanted = tuple(arg for arg in pargs[1:] if arg in options) or options
    element = render_contact_card(contact_id, wanted)
    return tostring(element).decode("utf-8")
