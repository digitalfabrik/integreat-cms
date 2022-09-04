import hashlib
import logging
import os

from django.conf import settings
from django.db.models import Min
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache

from weasyprint import HTML
from weasyprint.css.utils import InvalidValues
from weasyprint.images import ImageLoadingError


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
    For more information on weasyprint, see :doc:`weasyprint:index`

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
        if page_translation:
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
        try:
            pdf_content = HTML(string=html).write_pdf()
        except ImageLoadingError as e:
            logger.error(
                "Image loading error during pdf-conversion of %r, %r, %r: %s",
                region,
                language,
                pages,
                e,
            )
            return HttpResponse(_("The PDF could not be generated."), status=500)
        except InvalidValues as e:
            logger.error(
                "Invalid css-values during pdf-conversion of %r, %r, %r: %s",
                region,
                language,
                pages,
                e,
            )
            return HttpResponse(_("The PDF could not be generated."), status=500)
        # Write PDF content into file
        with pdf_storage.open(filename, "w+b") as pdf_file:
            pdf_file.write(pdf_content)
    return redirect(pdf_storage.url(filename))
