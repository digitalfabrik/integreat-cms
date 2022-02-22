"""
Helper functions for the XLIFF serializer
"""
import datetime
import difflib
import logging
import glob
import os
import uuid

from copy import deepcopy

from django.conf import settings
from django.contrib import messages
from django.core import serializers
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.forms.models import model_to_dict
from django.utils.translation import ugettext as _

from ..cms.constants import text_directions
from ..cms.forms import PageTranslationForm
from ..cms.models import Page, PageTranslation
from ..cms.utils.file_utils import create_zip_archive
from ..cms.utils.translation_utils import ugettext_many_lazy as __


upload_storage = FileSystemStorage(location=settings.XLIFF_UPLOAD_DIR)
download_storage = FileSystemStorage(
    location=settings.XLIFF_DOWNLOAD_DIR, base_url=settings.XLIFF_URL
)

logger = logging.getLogger(__name__)


def pages_to_xliff_file(request, pages, target_language):
    """
    Export a list of page IDs to a ZIP archive containing XLIFF files for a specified target language (or just a single
    XLIFF file if only one page is converted)

    :param request: The current request (used for error messages)
    :type request: ~django.http.HttpRequest

    :param pages: list of pages which should be translated
    :type pages: list [ ~integreat_cms.cms.models.pages.page.Page ]

    :param target_language: The target language (should not be the region's default language)
    :type target_language: :class:`~integreat_cms.cms.models.languages.language.Language`

    :return: The path of the generated zip file
    :rtype: str
    """
    logger.debug(
        "XLIFF export started by %r for pages %r and language %r",
        request.user,
        pages,
        target_language,
    )
    # Generate unique directory for this export
    dir_name = uuid.uuid4()
    # Create XLIFF files
    xliff_paths = {}
    for page in pages:
        try:
            xliff_paths[page] = page_to_xliff(page, target_language, dir_name)
        except RuntimeError as e:
            messages.error(request, e)
    # Check how many XLIFF files were created
    if len(xliff_paths) == 0:
        return None
    if len(xliff_paths) == 1:
        # If only one xliff file was created, return it directly instead of creating zip file
        page, xliff_file_path = xliff_paths.popitem()
        xliff_file_url = download_storage.url(
            os.path.relpath(xliff_file_path, settings.XLIFF_DOWNLOAD_DIR)
        )
        logger.info(
            "XLIFF export: %r converted to XLIFF file %r by %r",
            page,
            xliff_file_url,
            request.user,
        )
        return xliff_file_url
    # Generate file path for ZIP archive
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    region = pages[0].region
    zip_name = f"{region.slug}_{timestamp}_{region.get_source_language(target_language.slug).slug}_{target_language.slug}.zip"
    actual_filename = download_storage.save(f"{dir_name}/{zip_name}", ContentFile(""))
    # Create ZIP archive
    create_zip_archive(
        list(xliff_paths.values()), download_storage.path(actual_filename)
    )
    xliff_file_url = download_storage.url(actual_filename)
    logger.info(
        "XLIFF export: %r converted to XLIFF ZIP archive %r by %r",
        xliff_paths.keys(),
        xliff_file_url,
        request.user,
    )
    return xliff_file_url


def page_to_xliff(page, target_language, dir_name):
    """
    Export a page to an XLIFF file for a specified target language

    :param page: Page which should be translated
    :type page: ~integreat_cms.cms.models.pages.page.Page

    :param target_language: The target language (should not be the region's default language)
    :type target_language: :class:`~integreat_cms.cms.models.languages.language.Language`

    :param dir_name: The directory in which the xliff files should be created
    :type dir_name: uuid.UUID

    :raises RuntimeError: If the selected page translation does not have a source translation

    :return: The path of the generated XLIFF file
    :rtype: str
    """
    target_page_translation = page.get_translation(target_language.slug)
    if not target_page_translation:
        # Create temporary target translation
        target_page_translation = PageTranslation(
            page=page,
            language=target_language,
        )
    source_translation = target_page_translation.source_translation
    if not source_translation:
        source_language = page.region.get_source_language(target_language.slug)
        logger.warning(
            "Page translation %r does not have a source translation in %r and therefore cannot be exported to XLIFF.",
            target_page_translation,
            source_language,
        )
        raise RuntimeError(
            _(
                "Page {} does not have a source translation in {} and "
                "therefore cannot be exported as XLIFF for translation to {}."
            ).format(
                target_page_translation.readable_title, source_language, target_language
            )
        )

    try:
        xliff_content = serializers.serialize(
            settings.XLIFF_EXPORT_VERSION, [target_page_translation]
        )
    except Exception as e:
        # All these error should already have been prevented
        logger.exception(
            "An unexpected error has occurred while exporting %r to XLIFF: %s",
            target_page_translation,
            e,
        )
        raise RuntimeError(
            __(
                _("An unexpected error has occurred while exporting page {}.").format(
                    target_page_translation.readable_title
                ),
                _("Please try again or contact the administrator."),
            )
        ) from e

    filename = (
        f"{page.region.slug}_{source_translation.language.slug}_{target_language.slug}_"
        f"{page.id}_{source_translation.version}_{source_translation.slug}.xliff"
    )

    actual_filename = download_storage.save(
        f"{dir_name}/{filename}", ContentFile(xliff_content)
    )
    logger.debug("Created XLIFF file %r", actual_filename)

    # Set "currently in translation" status for existing target translation
    if target_page_translation.id:
        target_page_translation.currently_in_translation = True
        target_page_translation.save()

    return download_storage.path(actual_filename)


def xliffs_to_pages(request, xliff_dir):
    """
    Export a page to an XLIFF file for a specified target language

    :param request: The current request (used for error messages)
    :type request: ~django.http.HttpRequest

    :param xliff_dir: The directory containing the xliff files
    :type xliff_dir: str

    :return: A dict of all page translations as ``DeserializedObject``
    :rtype: dict
    """
    # Check if result is cached
    cached_result = cache.get(f"xliff-{xliff_dir}")
    if cached_result:
        logger.debug(
            "Returning cached result for deserializing all XLIFF files of %r",
            xliff_dir,
        )
        return cached_result
    # Get all xliff files in the given directory
    xliff_file_paths = glob.glob(xliff_dir + "/**/*.xliff", recursive=True)
    page_translations = {}
    for xliff_file_path in xliff_file_paths:
        with open(xliff_file_path, "r", encoding="utf-8") as xliff_file:
            logger.debug(
                "Deserializing XLIFF file %r",
                xliff_file_path,
            )
            xliff_file_path_rel = os.path.relpath(xliff_file_path, xliff_dir)
            try:
                # Try to deserialize the file
                page_translations[xliff_file_path_rel] = list(
                    serializers.deserialize("xliff", xliff_file.read())
                )
            except Page.DoesNotExist:
                logger.error(
                    "The page of XLIFF file %r does not exist.",
                    xliff_file_path,
                )
                messages.error(
                    request,
                    __(
                        _(
                            'The page referenced in XLIFF file "{}" could not be found.'
                        ).format(xliff_file_path_rel),
                        _("Please contact the administrator."),
                    ),
                )
            # In this case, we want to catch all exceptions because the import of the other files should work even if
            # some xliff files are broken or other unexpected errors occur
            except Exception as e:  # pylint: disable=broad-except
                # All these error should already have been prevented, so probably the XLIFF file is broken.
                logger.exception(
                    "An unexpected error has occurred while importing XLIFF file %r: %s",
                    xliff_file_path,
                    e,
                )
                messages.error(
                    request,
                    __(
                        _(
                            'An unexpected error has occurred while importing XLIFF file "{}".'
                        ).format(xliff_file_path_rel),
                        _("Please try again or contact the administrator."),
                    ),
                )
    # Store deserialized objects in cache
    cache.set(f"xliff-{xliff_dir}", page_translations)
    return page_translations


def get_xliff_import_diff(request, xliff_dir):
    """
    Show the XLIFF import diff

    :param request: The current request (used for error messages)
    :type request: ~django.http.HttpRequest

    :param xliff_dir: The directory containing the xliff files
    :type xliff_dir: str

    :return: A dict containing data about the imported xliff files
    :rtype: dict
    """
    diff = []
    for xliff_file, deserialized_objects in xliffs_to_pages(request, xliff_dir).items():
        for deserialized in deserialized_objects:
            page_translation = deserialized.object
            existing_translation = page_translation.latest_version or PageTranslation(
                page=page_translation.page,
                language=page_translation.language,
            )
            diff.append(
                {
                    "file": xliff_file,
                    "existing": existing_translation,
                    "import": page_translation,
                    "source_diff": {
                        "title": "\n".join(
                            list(
                                difflib.unified_diff(
                                    [existing_translation.title],
                                    [page_translation.title],
                                    lineterm="",
                                )
                            )[2:]
                        ),
                        "content": "\n".join(
                            list(
                                difflib.unified_diff(
                                    existing_translation.content.splitlines(),
                                    page_translation.content.splitlines(),
                                    lineterm="",
                                )
                            )[2:]
                        ),
                    },
                    "right_to_left": page_translation.language.text_direction
                    == text_directions.RIGHT_TO_LEFT,
                    "errors": get_xliff_import_errors(request, page_translation),
                }
            )
    return diff


def xliff_import_confirm(request, xliff_dir):
    """
    Confirm the XLIFF import and write changes to database

    :param request: The current request (used for error messages)
    :type request: ~django.http.HttpRequest

    :param xliff_dir: The directory containing the xliff files
    :type xliff_dir: str

    :return: A dict containing data about the imported xliff files
    :rtype: dict
    """
    success = True
    # Iterate over all xliff files
    for xliff_file, deserialized_objects in xliffs_to_pages(request, xliff_dir).items():
        # Iterate over all objects of one xliff file
        # (typically, one xliff file contains exactly one page translation)
        for deserialized in deserialized_objects:
            page_translation = deserialized.object
            errors = get_xliff_import_errors(request, page_translation)
            if errors:
                logger.warning(
                    "XLIFF import of %r not possible because validation of %r failed with the errors: %r",
                    xliff_file,
                    page_translation,
                    errors,
                )
                error_list = "<ul>"
                for error in errors:
                    error_list += f"<li><i data-feather='alert-triangle' class='pb-1'></i> {error['message']}</li>"
                error_list += "</ul>"
                messages.error(
                    request,
                    _(
                        "Page {} could not be imported successfully because of the errors: {}"
                    ).format(page_translation.readable_title, error_list),
                )
                success = False
            else:
                # Confirm import and write changes to the database
                page_translation.save()
                logger.info(
                    "%r of XLIFF file %r was imported successfully by %r",
                    page_translation,
                    xliff_file,
                    request.user,
                )
                messages.success(
                    request,
                    _("Page {} was imported successfully.").format(
                        page_translation.readable_title
                    ),
                )
    return success


def get_xliff_import_errors(request, page_translation):
    """
    Validate an imported page translation and return all errors

    :param request: The current request (used for error messages)
    :type request: ~django.http.HttpRequest

    :param page_translation: The page translation which is being imported
    :type page_translation: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

    :return: All errors of this XLIFF import
    :rtype: list [ dict ]
    """
    error_messages = []
    # Get current region
    region = request.region
    # Check whether user can import the page translation
    if not request.user.has_perm("cms.change_page_object", page_translation.page):
        error_messages.append(
            {
                "level_tag": "error",
                "message": _(
                    "You don't have the permission to import this page."
                ).format(page_translation.readable_title),
            }
        )
    # Check whether the page translation belongs to the current region
    if not page_translation.page.region == region:
        error_messages.append(
            {
                "level_tag": "error",
                "message": _("This page belongs to another region ({}).").format(
                    page_translation.page.region.full_name,
                ),
            }
        )
    # Retrieve existing page translation in the target language
    # (using model instances in forms may change them, so we need to copy it in order to not change the cached property)
    existing_translation = deepcopy(page_translation.latest_version)
    # Validate page translation
    page_translation_form = PageTranslationForm(
        data=model_to_dict(page_translation),
        instance=existing_translation,
        additional_instance_attributes={
            "creator": request.user,
            "language": page_translation.language,
            "page": page_translation.page,
        },
    )
    if not page_translation_form.is_valid():
        error_messages.extend(
            [
                {"level_tag": message["type"], "message": message["text"]}
                for message in page_translation_form.get_error_messages()
            ]
        )
    if not page_translation_form.has_changed():
        error_messages.append(
            {
                "level_tag": "info",
                "message": _("No changes detected."),
            }
        )
    return error_messages
