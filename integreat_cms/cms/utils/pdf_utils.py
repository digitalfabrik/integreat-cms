from __future__ import annotations

import contextlib
import hashlib
import logging
import mimetypes
import os
import tempfile
from functools import cache
from typing import Any, TYPE_CHECKING
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _
from weasyprint import HTML
from weasyprint.urls import URLFetcher, URLFetcherResponse

from ..constants import status, text_directions
from ..models import Language, Page, PageTranslation
from .text_utils import truncate_bytewise

if TYPE_CHECKING:
    from django.http.response import HttpResponseRedirect

    from ..models import Region
    from ..models.pages.page import PageQuerySet

logger = logging.getLogger(__name__)

_pdf_storage = FileSystemStorage(location=settings.PDF_ROOT, base_url=settings.PDF_URL)

_PDF_EXT = ".pdf"


@cache
def _max_pdf_name_length() -> int:
    """
    Get the maximum length of a PDF filename (without extension). The value only
    depends on the file system of :data:`~integreat_cms.core.settings.PDF_ROOT`,
    so it is computed once per process.

    :return: The maximum filename length in bytes
    """
    # Make sure, that the length of the filename is valid. To prevent potential
    # edge cases, shorten filenames to 3/4 of the allowed max length.
    try:
        return ((os.statvfs(settings.PDF_ROOT).f_namemax // 4) * 3) - len(_PDF_EXT)
    except FileNotFoundError:
        return 192 - len(_PDF_EXT)


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


def _compute_pdf_hash(
    region: Region,
    language_slug: str,
    pages: PageQuerySet,
) -> tuple[str, PageQuerySet, list[tuple]]:
    """
    Build the deterministic hash value that identifies the PDF to (re)generate
    for a set of pages in a region/language combination.

    The hash covers the region (slug + ``last_updated``) and, for every page
    in ``pages`` that (a) has a public translation in ``language_slug`` and
    (b) is not archived (explicitly or via an ancestor), the public
    translation's id and ``last_updated``. Pages that fail either condition
    are excluded from the result queryset.

    :param region: owning region
    :param language_slug: bcp47 slug of the language the PDF is rendered in
    :param pages: pages to include in the hash (order is (tree_id, lft))
    :return: the 10-char hash substring, the filtered ``pages`` queryset, and
             the list of per-page tuples ``(page_id, depth, lft, rgt, tree_id,
             explicitly_archived, title, translation_id, translation_updated)``
             for inclusion in the title computation
    """
    pdf_key_list: list[object] = [region.slug, region.last_updated]
    page_translation_rows = list(
        PageTranslation.objects.filter(
            language__slug=language_slug,
            status=status.PUBLIC,
            page__in=pages,
        )
        .order_by("page__id", "-version")
        .values_list(
            "page__id",
            "page__depth",
            "page__lft",
            "page__rgt",
            "page__tree_id",
            "page__explicitly_archived",
            "title",
            "id",
            "last_updated",
        )
        .distinct("page__id")
    )
    page_translation_rows.sort(key=lambda r: (r[4] or 0, r[2] or 0))

    explicitly_archived = [(r[2], r[3]) for r in page_translation_rows if r[5]]

    def _is_archived(lft: int, rgt: int) -> bool:
        return any(el < lft and rgt < er for (el, er) in explicitly_archived)

    included_rows = [
        r for r in page_translation_rows if not r[5] and not _is_archived(r[2], r[3])
    ]

    for r in included_rows:
        pdf_key_list.append(r[7])  # translation id
        pdf_key_list.append(r[8])  # translation last_updated

    pages = pages.filter(id__in=[r[0] for r in included_rows])

    pdf_key_string = "_".join(map(str, pdf_key_list))
    pdf_hash = hashlib.sha256(bytes(pdf_key_string, "utf-8")).hexdigest()[:10]
    return pdf_hash, pages, included_rows


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
    # (see :func:`compute_pdf_hash` for the actual hash construction).
    pdf_hash, pages, included_translations = _compute_pdf_hash(
        region, language_slug, pages
    )

    if not (amount_pages := pages.count()):
        return HttpResponse(
            _("No valid pages selected for PDF generation."),
            status=400,
        )
    language = Language.objects.get(slug=language_slug)
    filename = build_pdf_filename(
        region, language, included_translations, amount_pages, pdf_hash
    )
    # Only generate new pdf if not already exists
    if not _pdf_storage.exists(filename):
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
            return HttpResponse(
                _("The PDF could not be successfully generated."),
                status=500,
            )
    return redirect(_pdf_storage.url(filename))


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
    included_translations: list[tuple],
    amount_pages: int,
    pdf_hash: str,
) -> str:
    """
    Build the cached PDF filename, including a content hash prefix.

    :param region: The region of the export
    :param language: The language of the export
    :param included_translations: The translation rows returned by :func:`_compute_pdf_hash`
    :param amount_pages: How many pages are included
    :param pdf_hash: Hash of the selected translations
    :return: Relative path inside the PDF storage
    """
    # Build the title from the already-fetched rows (no extra queries).
    if amount_pages == 1:
        # If pdf contains only one page, take its title as filename
        title = included_translations[0][6]
    else:
        # If pdf contains multiple pages, check the minimum level
        min_level = min(r[1] for r in included_translations)
        min_level_rows = [r for r in included_translations if r[1] == min_level]
        # If there's exactly one page with the minimum level, take its title;
        # otherwise, fall back to the region name
        title = min_level_rows[0][6] if len(min_level_rows) == 1 else region.name
    name = f"{settings.BRANDING_TITLE} - {language.translated_name} - {title}"
    return f"{pdf_hash}/{truncate_bytewise(name, _max_pdf_name_length())}{_PDF_EXT}"


def write_pdf(html: str, filename: str) -> None:
    """
    Convert HTML to PDF and store it in :data:`~integreat_cms.core.settings.PDF_ROOT`.

    :param html: The rendered HTML document
    :param filename: Relative path inside the PDF storage
    """
    # Render into a temporary file in the target directory and move it into place
    # when done, so concurrent requests never see a partially written PDF.
    final_path = _pdf_storage.path(filename)
    directory = os.path.dirname(final_path)
    os.makedirs(directory, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=".", suffix=".part", dir=directory)
    try:
        with os.fdopen(tmp_fd, "w+b") as pdf_file:
            HTML(
                string=html,
                base_url=settings.BASE_URL,
                url_fetcher=PdfUrlFetcher(),
            ).write_pdf(
                target=pdf_file,
                # Apply HTML attributes like the width and height of images
                presentational_hints=True,
            )
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, final_path)  # atomic publish (same directory)
    finally:
        # Present only if rendering raised above.
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)  # no-op once os.replace() moved it


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
