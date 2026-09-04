from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import render
from django.views.generic.base import TemplateView
from lxml.html import fromstring

from ...models import Contact, Event, Page, Place
from ...utils.link_utils import format_phone_number
from ...utils.linkcheck_utils import get_link_query

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest
    from django.template.response import TemplateResponse
    from linkcheck import Link, Url


def used_as_simple_link(link_object: Link) -> bool:
    """
    A function to check whether the given link is used as simple link (not as a part of contact card)
    """
    for elem, _, link, _ in fromstring(link_object.content_object.content).iterlinks():
        if link == link_object.url.url and (
            not elem.getparent().getparent()
            or "contact-card" not in elem.getparent().getparent().classes
        ):
            return True
    return False


def clean_url(url: Url) -> str:
    """
    Remove the prefix tel:, +49 and mailto:

    :param url: The URL object
    :return: URL string without prefix
    """

    if url.type == "phone":
        return format_phone_number(url.url.lstrip("tel:"))
    if url.type == "mailto":
        return url.url[7:]
    return url.url


class PotentialContactSourcesView(TemplateView):
    """
    View for the contact suggestion
    """

    template_name = "contacts/contact_from_email_and_phone.html"
    extra_context = {
        "current_menu_item": "contacts",
    }

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> TemplateResponse:
        r"""
        Render the contact suggestion

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region_links = get_link_query([request.region])
        email_or_phone_links = region_links.filter(
            Q(url__url__startswith="mailto") | Q(url__url__startswith="tel")
        )

        page_translation_content_type_id = ContentType.objects.get(
            model="pagetranslation"
        ).id
        event_translation_content_type_id = ContentType.objects.get(
            model="eventtranslation"
        ).id
        place_translation_content_type_id = ContentType.objects.get(
            model="placetranslation"
        ).id

        links_in_pages = email_or_phone_links.filter(
            content_type=page_translation_content_type_id
        )
        links_in_events = email_or_phone_links.filter(
            content_type=event_translation_content_type_id
        )
        links_in_places = email_or_phone_links.filter(
            content_type=place_translation_content_type_id
        )

        page_ids = (
            links_in_pages.order_by()
            .values_list("page_translation__page", flat=True)
            .distinct()
        )
        links_per_page = []
        for page_id in page_ids:
            page = Page.objects.filter(id=page_id).first()
            page_links = (
                links_in_pages.filter(page_translation__page=page_id)
                .order_by()
                .distinct("url__url", "page_translation")
            )
            links = {
                clean_url(link.url) for link in page_links if used_as_simple_link(link)
            }
            contacts = Contact.objects.filter(place__region=request.region).filter(
                Q(email__in=links) | Q(phone_number__in=links)
            )
            if links:
                links_per_page += [(page, links, contacts)]

        event_ids = (
            links_in_events.order_by()
            .values_list("event_translation__event", flat=True)
            .distinct()
        )
        links_per_event = []
        for event_id in event_ids:
            event = Event.objects.filter(id=event_id).first()
            event_links = (
                links_in_events.filter(event_translation__event=event_id)
                .order_by()
                .distinct("url__url", "event_translation")
            )
            links = {
                clean_url(link.url) for link in event_links if used_as_simple_link(link)
            }
            contacts = Contact.objects.filter(place__region=request.region).filter(
                Q(email__in=links) | Q(phone_number__in=links)
            )
            if links:
                links_per_event += [(event, links, contacts)]

        place_ids = (
            links_in_places.order_by()
            .values_list("place_translation__place", flat=True)
            .distinct()
        )
        links_per_place = []
        for place_id in place_ids:
            place = Place.objects.filter(id=place_id).first()
            place_links = (
                links_in_places.filter(place_translation__place=place_id)
                .order_by()
                .distinct("url__url", "place_translation")
            )
            links = {
                clean_url(link.url) for link in place_links if used_as_simple_link(link)
            }
            contacts = Contact.objects.filter(place__region=request.region).filter(
                Q(email__in=links) | Q(phone_number__in=links)
            )
            if links:
                links_per_place += [(place, links, contacts)]

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "links_per_page": links_per_page,
                "links_per_event": links_per_event,
                "links_per_place": links_per_place,
                "wanted": [
                    "area_of_responsibility",
                    "name",
                    "email",
                    "phone_number",
                    "website",
                ],
            },
        )
