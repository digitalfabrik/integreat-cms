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

    * ``only_address``             (optional) – Whether the address             should be shown and other, not explicitly wanted details should be hidden
    * ``only_email``               (optional) – Whether the email address       should be shown and other, not explicitly wanted details should be hidden
    * ``only_phone_number``        (optional) – Whether the phone number        should be shown and other, not explicitly wanted details should be hidden
    * ``only_mobile_phone_number`` (optional) – Whether the mobile phone number should be shown and other, not explicitly wanted details should be hidden
    * ``only_website``             (optional) – Whether the website             should be shown and other, not explicitly wanted details should be hidden
    """
    contact_id = pargs[0]
    options = (
        "address",
        "email",
        "phone_number",
        "mobile_phone_number",
        "website",
    )
    wanted = (
        tuple(filter(lambda arg: arg.removeprefix("only_") in options, pargs[1:]))
        or options
    )
    element = render_contact_card(contact_id, wanted)
    return tostring(element).decode("utf-8")
