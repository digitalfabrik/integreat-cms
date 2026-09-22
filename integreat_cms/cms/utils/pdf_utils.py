from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
from io import BytesIO
from typing import Any, TYPE_CHECKING
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db.models import Min
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _
from weasyprint import HTML
from weasyprint.urls import URLFetcher, URLFetcherResponse

from ..constants import text_directions
from ..models import Language, Page
from .text_utils import truncate_bytewise

if TYPE_CHECKING:
    from django.http.response import HttpResponseRedirect

    from ..models import Region
    from ..models.pages.page import PageQuerySet

logger = logging.getLogger(__name__)

pdf_storage = FileSystemStorage(location=settings.PDF_ROOT, base_url=settings.PDF_URL)


class PdfUrlFetcher(URLFetcher):
    """
    Resolve Django static and media files for WeasyPrint, then fall back to HTTP.
    """

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> Any:
        """
        Fetch a resource by URL for PDF rendering.

        :param url: The absolute URL WeasyPrint wants to load
        :param headers: Optional extra HTTP headers for remote fetches
        :return: The fetched resource
        """
        if path := resolve_pdf_uri(url):
            guessed_type, _encoding = mimetypes.guess_type(path)
            with open(path, "rb") as resource:
                body = resource.read()
            return URLFetcherResponse(
                url,
                body,
                {"Content-Type": guessed_type or "application/octet-stream"},
            )
        return super().fetch(url, headers)


def generate_pdf(
    region: Region,
    language_slug: str,
    pages: PageQuerySet,
) -> HttpResponseRedirect | HttpResponse:
    """
    Function for handling a pdf export request for pages.
    The pages were either selected by cms user or by API request (see :func:`~integreat_cms.api.v3.pdf_export`)
    For more information on WeasyPrint, see :doc:`weasyprint:index`

    :param region: region which requested the pdf document
    :param language_slug: bcp47 slug of the current language
    :param pages: at least one page to render as PDF document
    :return: Redirection to PDF document, or an error response
    """
    # first all necessary data for hashing are collected, starting at region slug
    # region last_updated field taking into account, to keep track of maybe edited region icons
    pdf_key_list = [region.slug, region.last_updated]
    for page in pages:
        # add translation id and last_updated to hash key list if they exist
        page_translation = page.get_public_translation(language_slug)
        if page_translation and not page.archived:
            # if translation for this language exists
            pdf_key_list.append(page_translation.id)
            pdf_key_list.append(page_translation.last_updated)
        else:
            # if the page has no translation for this language
            pages = pages.exclude(id=page.id)
    # finally combine all list entries to a single hash key
    pdf_key_string = "_".join(map(str, pdf_key_list))
    # compute the hash value based on the hash key
    pdf_hash = hashlib.sha256(bytes(pdf_key_string, "utf-8")).hexdigest()[:10]
    if not (amount_pages := pages.count()):
        return HttpResponse(
            _("No valid pages selected for PDF generation."),
            status=400,
        )
    language = Language.objects.get(slug=language_slug)
    filename = build_pdf_filename(region, language, pages, amount_pages, pdf_hash)
    # Only generate new pdf if not already exists
    if not pdf_storage.exists(filename):
        html = render_pdf_html(region, language, pages, amount_pages)
        try:
            write_pdf(html, filename)
        except Exception:
            logger.exception(
                "The following PDF could not be rendered: %r, %r, %r",
                region,
                language,
                pages,
            )
            if pdf_storage.exists(filename):
                pdf_storage.delete(filename)
            return HttpResponse(
                _("The PDF could not be successfully generated."),
                status=500,
            )
    return redirect(pdf_storage.url(filename))


def render_pdf_html(
    region: Region,
    language: Language,
    pages: PageQuerySet,
    amount_pages: int,
) -> str:
    """
    Render the HTML source that is converted to PDF.

    :param region: The region of the export
    :param language: The language of the export
    :param pages: The pages to include
    :param amount_pages: How many pages are included
    :return: The rendered HTML
    """
    annotated_pages = Page.get_annotated_list_qs(pages)
    context = {
        "right_to_left": language.text_direction == text_directions.RIGHT_TO_LEFT,
        "region": region,
        "annotated_pages": annotated_pages,
        "language": language,
        "amount_pages": amount_pages,
        "prevent_italics": ["ar", "fa"],
        "BRANDING": settings.BRANDING,
        "BRANDING_TITLE": settings.BRANDING_TITLE,
    }
    return get_template("pages/page_pdf.html").render(context)


def build_pdf_filename(
    region: Region,
    language: Language,
    pages: PageQuerySet,
    amount_pages: int,
    pdf_hash: str,
) -> str:
    """
    Build the cached PDF filename, including a content hash prefix.

    :param region: The region of the export
    :param language: The language of the export
    :param pages: The pages to include
    :param amount_pages: How many pages are included
    :param pdf_hash: Hash of the selected translations
    :return: Relative path inside the PDF storage
    """
    if amount_pages == 1:
        # If pdf contains only one page, take its title as filename
        title = pages.first().get_public_translation(language.slug).title
    else:
        # If pdf contains multiple pages, check the minimum level
        min_level = pages.aggregate(Min("depth")).get("depth__min")
        # Query all pages with this minimum level
        min_level_pages = pages.filter(depth=min_level)
        if min_level_pages.count() == 1:
            # If there's exactly one page with the minimum level, take its title
            title = min_level_pages.first().get_public_translation(language.slug).title
        else:
            # In any other case, take the region name
            title = region.name
    # Make sure, that the length of the filename is valid. To prevent potential
    # edge cases, shorten filenames to 3/4 of the allowed max length.
    ext = ".pdf"
    try:
        max_len = ((os.statvfs(settings.PDF_ROOT).f_namemax // 4) * 3) - len(ext)
    except FileNotFoundError:
        max_len = 192 - len(ext)
    name = f"{settings.BRANDING_TITLE} - {language.translated_name} - {title}"
    return f"{pdf_hash}/{truncate_bytewise(name, max_len)}{ext}"


def write_pdf(html: str, filename: str) -> None:
    """
    Convert HTML to PDF and store it in :data:`~integreat_cms.core.settings.PDF_ROOT`.

    :param html: The rendered HTML document
    :param filename: Relative path inside the PDF storage
    """
    pdf_bytes = BytesIO()
    HTML(
        string=html,
        base_url=settings.BASE_URL,
        url_fetcher=PdfUrlFetcher(),
    ).write_pdf(
        target=pdf_bytes,
        # Apply HTML attributes like the width and height of images
        presentational_hints=True,
    )
    pdf_storage.save(filename, ContentFile(pdf_bytes.getvalue()))


def resolve_pdf_uri(uri: str) -> str | None:
    """
    Resolve a WeasyPrint resource URL to a local filesystem path.

    Remote URLs that are not hosted on this application are left to the default
    fetcher by returning ``None``.

    :param uri: URI generated by Django (static/media) or resolved against ``BASE_URL``
    :return: Absolute filesystem path, or ``None`` if the URL is remote or missing
    """
    parsed_uri = urlparse(uri)
    if parsed_uri.hostname:
        # When the uri is an absolute URL to an external host, let WeasyPrint fetch it.
        if parsed_uri.hostname not in settings.ALLOWED_HOSTS:
            return None
        # When the uri is an absolute URL to an allowed host, convert it to an absolute local path
        uri = parsed_uri.path
        # When the url contains the legacy media url, replace it with the new pattern
        if (LEGACY_MEDIA_URL := "/wp-content/uploads/sites/") in uri:
            uri = f"/media/regions/{uri.partition(LEGACY_MEDIA_URL)[2]}"
    if uri.startswith(settings.MEDIA_URL):
        # Get absolute path for media files
        path = unquote(
            os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, "")),
        )
        # make sure that file exists
        if not os.path.isfile(path):
            logger.error(
                "The file %r was not found in the media directories.",
                path[:1024],
            )
            return None
        return path
    if uri.startswith(settings.STATIC_URL):
        # Remove the STATIC_URL from the start of the uri
        uri = uri[len(settings.STATIC_URL) :]
    elif uri.startswith("../"):
        # Remove ../ from the start of the uri
        uri = uri[3:]
    elif not uri.startswith("assets/"):
        logger.warning(
            "The file %r is not inside the static directories %r and %r.",
            uri[:1024],
            settings.STATIC_URL,
            settings.MEDIA_URL,
        )
        return None
    if not (result := finders.find(uri)):
        logger.error(
            "The file %r was not found in the static directories %r.",
            uri[:1024],
            finders.searched_locations,
        )
        return None
    return result
