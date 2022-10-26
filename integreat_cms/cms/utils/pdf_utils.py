import hashlib
import logging
import os

from urllib.parse import urlparse, unquote

from django.conf import settings
from django.contrib.staticfiles import finders
from django.db.models import Min
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from xhtml2pdf import pisa
from xhtml2pdf.default import DEFAULT_CSS


from .text_utils import truncate_bytewise
from ..constants import text_directions
from ..models import Language, Page

logger = logging.getLogger(__name__)

pdf_storage = FileSystemStorage(location=settings.PDF_ROOT, base_url=settings.PDF_URL)


@never_cache
# pylint: disable=too-many-locals
def generate_pdf(region, language_slug, pages):
    """
    Function for handling a pdf export request for pages.
    The pages were either selected by cms user or by API request (see :func:`~integreat_cms.api.v3.pdf_export`)
    For more information on xhtml2pdf, see :doc:`xhtml2pdf:index`

    :param region: region which requested the pdf document
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :param language_slug: bcp47 slug of the current language
    :type language_slug: str

    :param pages: at least on page to render as PDF document
    :type pages: ~treebeard.ns_tree.NS_NodeQuerySet

    :return: Redirection to PDF document
    :rtype: ~django.http.HttpResponseRedirect
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
    amount_pages = pages.count()
    if amount_pages == 0:
        return HttpResponse(
            _("No valid pages selected for PDF generation."), status=400
        )
    if amount_pages == 1:
        # If pdf contains only one page, take its title as filename
        title = pages.first().get_public_translation(language_slug).title
    else:
        # If pdf contains multiple pages, check the minimum level
        min_level = pages.aggregate(Min("depth")).get("depth__min")
        # Query all pages with this minimum level
        min_level_pages = pages.filter(depth=min_level)
        if min_level_pages.count() == 1:
            # If there's exactly one page with the minimum level, take its title
            title = min_level_pages.first().get_public_translation(language_slug).title
        else:
            # In any other case, take the region name
            title = region.name
    language = Language.objects.get(slug=language_slug)
    # Make sure, that the length of the filename is valid. To prevent potential
    # edge cases, shorten filenames to 3/4 of the allowed max length.
    ext = ".pdf"
    try:
        max_len = ((os.statvfs(settings.PDF_ROOT).f_namemax // 4) * 3) - len(ext)
    except FileNotFoundError:
        max_len = 192 - len(ext)
    name = f"{capfirst(settings.BRANDING)} - {language.translated_name} - {title}"
    filename = f"{pdf_hash}/{truncate_bytewise(name, max_len)}{ext}"
    # Only generate new pdf if not already exists
    if not pdf_storage.exists(filename):
        # Convert queryset to annotated list which can be rendered better
        annotated_pages = Page.get_annotated_list_qs(pages)
        context = {
            "right_to_left": language.text_direction == text_directions.RIGHT_TO_LEFT,
            "region": region,
            "annotated_pages": annotated_pages,
            "language": language,
            "amount_pages": amount_pages,
            "prevent_italics": ["ar", "fa"],
            "BRANDING": settings.BRANDING,
        }
        html = get_template("pages/page_pdf.html").render(context)
        # Save empty file
        pdf_storage.save(filename, ContentFile(""))

        # Get fixed version of default pdf styling (see https://github.com/digitalfabrik/integreat-cms/issues/1537)
        fixed_css = DEFAULT_CSS.replace("background-color: transparent;", "", 1)

        # Write PDF content into file
        with pdf_storage.open(filename, "w+b") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html,
                dest=pdf_file,
                link_callback=link_callback,
                encoding="UTF-8",
                default_css=fixed_css,
            )
        # pylint: disable=no-member
        if pisa_status.err:
            logger.error(
                "The following PDF could not be rendered: %r, %r, %r",
                region,
                language,
                pages,
            )
            return HttpResponse(
                _("The PDF could not be successfully generated."), status=500
            )
    return redirect(pdf_storage.url(filename))


# pylint: disable=unused-argument
def link_callback(uri, rel):
    """
    According to xhtml2pdf documentation (see :doc:`xhtml2pdf:usage`),
    this function is necessary for resolving the django static files references.
    It returns the absolute paths to the files on the file system.

    :param uri: URI that is generated by django template tag 'static'
    :type uri: str

    :param rel: The relative path directory
    :type rel: str

    :return: The absolute path on the file system according to django's static file settings
    :rtype: str
    """
    parsed_uri = urlparse(uri)
    # When the uri is an absolute URL to an allowed host, convert it to an absolute local path
    if parsed_uri.hostname in settings.ALLOWED_HOSTS:
        uri = parsed_uri.path
        # When the url contains the legacy media url, replace it with the new pattern
        LEGACY_MEDIA_URL = "/wp-content/uploads/sites/"
        if LEGACY_MEDIA_URL in uri:
            uri = f"/media/regions/{uri.partition(LEGACY_MEDIA_URL)[2]}"
    if uri.startswith(settings.MEDIA_URL):
        # Get absolute path for media files
        path = unquote(
            os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        )
        # make sure that file exists
        if not os.path.isfile(path):
            logger.exception(
                "The file %r was not found in the media directories.", path
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
            uri,
            settings.STATIC_URL,
            settings.MEDIA_URL,
        )
        return uri
    result = finders.find(uri)
    if not result:
        logger.exception(
            "The file %r was not found in the static directories %r.",
            uri,
            finders.searched_locations,
        )
    return result
