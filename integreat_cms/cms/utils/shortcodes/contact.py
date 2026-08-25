"""
This module contains the shortcode which references a :class:`~integreat_cms.cms.models.contact.contact.Contact`
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lxml.html import tostring

from ..content_utils import render_contact_card
from .base import register, Shortcode

if TYPE_CHECKING:
    from typing import Any, Final

#: The details of a contact which can be requested individually
CONTACT_DETAILS: Final[tuple[str, ...]] = (
    "address",
    "email",
    "phone_number",
    "mobile_phone_number",
    "website",
)


@register
class ContactShortcode(Shortcode):
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

    keyword = "contact"

    def expand(
        self,
        pargs: list[str],
        kwargs: dict[str, str],  # noqa: ARG002
        context: dict[str, Any] | None,  # noqa: ARG002
    ) -> str:
        """
        Expand the shortcode into the rendered contact card

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param context: The context the shortcode is expanded in
        :return: The rendered contact card
        """
        contact_id = pargs[0] if pargs else None
        wanted = (
            tuple(arg for arg in pargs[1:] if arg in CONTACT_DETAILS) or CONTACT_DETAILS
        )
        return tostring(render_contact_card(contact_id, wanted)).decode("utf-8")
