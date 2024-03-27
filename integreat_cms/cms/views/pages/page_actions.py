"""
This module contains view actions related to pages.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import TYPE_CHECKING

from db_mutex import DBMutexError, DBMutexTimeoutError
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from treebeard.exceptions import InvalidMoveToDescendant, InvalidPosition

from ....api.decorators import json_response
from ...constants import text_directions
from ...decorators import permission_required
from ...forms import PageForm
from ...models import Page, PageTranslation, Region
from ...utils.file_utils import extract_zip_archive

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


@require_POST
def archive_page(
    request: HttpRequest, page_id: int, region_slug: str, language_slug: str
) -> HttpResponseRedirect:
    """
    Archive page object

    :param request: The current request
    :param page_id: The id of the page which should be archived
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    """
    region = request.region
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.change_page_object", page):
        raise PermissionDenied(
            f"{request.user!r} does not have the permission to archive {page!r}"
        )

    if page.mirroring_pages.exists():
        messages.error(
            request,
            _(
                "This page cannot be archived because it was embedded as live content from another page."
            ),
        )
    else:
        page.archive()

        logger.debug("%r archived by %r", page, request.user)
        messages.success(request, _("Page was successfully archived"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
def restore_page(
    request: HttpRequest, page_id: int, region_slug: str, language_slug: str
) -> HttpResponseRedirect:
    """
    Restore page object (set ``archived=False``)

    :param request: The current request
    :param page_id: The id of the page which should be restored
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    """

    region = request.region
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.change_page_object", page):
        raise PermissionDenied(
            f"{request.user!r} does not have the permission to restore {page!r}"
        )

    page.restore()

    if page.implicitly_archived:
        logger.debug(
            "%r restored by %r but still implicitly archived",
            page,
            request.user,
        )
        messages.info(
            request,
            _("Page was successfully restored.")
            + " "
            + _(
                "However, it is still archived because one of its parent pages is archived."
            ),
        )
        return redirect(
            "archived_pages",
            **{
                "region_slug": region_slug,
                "language_slug": language_slug,
            },
        )

    logger.debug("%r restored by %r", page, request.user)
    messages.success(request, _("Page was successfully restored."))
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@permission_required("cms.view_page")
@json_response
# pylint: disable=unused-argument
def preview_page_ajax(
    request: HttpRequest, page_id: int, region_slug: str, language_slug: str
) -> JsonResponse:
    """
    Preview page object

    :param request: The current request
    :param page_id: The id of the page which should be viewed
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :raises ~django.http.Http404: HTTP status 404 if page translation does not exist

    :return: Significant page data as a JSON.
    """
    region = request.region
    page = get_object_or_404(region.pages, id=page_id)

    if page_translation := page.get_translation(language_slug):
        mirrored_translation = page.get_mirrored_page_translation(language_slug)
        return JsonResponse(
            data={
                "title": page_translation.title,
                "page_translation": page_translation.content,
                "mirrored_translation": (
                    mirrored_translation.content if mirrored_translation else ""
                ),
                "mirrored_page_first": page.mirrored_page_first,
                "right_to_left": (
                    page_translation.language.text_direction
                    == text_directions.RIGHT_TO_LEFT
                    if page_translation
                    else False
                ),
            }
        )
    raise Http404("Translation of the given page could not be found")


@permission_required("cms.view_page")
@json_response
# pylint: disable=unused-argument
def get_page_content_ajax(
    request: HttpRequest, region_slug: str, language_slug: str, page_id: int
) -> JsonResponse:
    """
    Get content of a page translation based on language slug

    :param request: The current request
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :param page_id: The id of the page which should be viewed
    :raises ~django.http.Http404: HTTP status 404 if page translation does not exist

    :return: Page translation content as a JSON.
    """
    region = request.region
    page = get_object_or_404(region.pages, id=page_id)
    if page_translation := page.get_translation(language_slug):
        return JsonResponse(data={"content": page_translation.content})
    raise Http404("Translation of the given page could not be found")


@require_POST
@permission_required("cms.delete_page")
@transaction.atomic
def delete_page(
    request: HttpRequest, page_id: int, region_slug: str, language_slug: str
) -> HttpResponseRedirect:
    """
    Delete page object

    :param request: The current request
    :param page_id: The id of the page which should be deleted
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    """

    region = request.region
    page = get_object_or_404(region.pages, id=page_id)

    if page.children.exists():
        messages.error(request, _("You cannot delete a page which has subpages."))
    elif page.mirroring_pages.exists():
        messages.error(
            request,
            _(
                "This page cannot be deleted because it was embedded as live content from another page."
            ),
        )
    else:
        logger.info("%r deleted by %r", page, request.user)
        page.delete()
        messages.success(request, _("Page was successfully deleted"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


def expand_page_translation_id(
    request: HttpRequest, short_url_id: int
) -> HttpResponseRedirect:
    """
    Searches for a page translation with corresponding ID and redirects browser to web app

    :param request: The current request
    :param short_url_id: The id of the requested page
    :return: A redirection to :class:`~integreat_cms.core.settings.WEBAPP_URL`
    """

    page_translation = PageTranslation.objects.get(id=short_url_id).public_version

    if page_translation and not page_translation.page.archived:
        return redirect(settings.WEBAPP_URL + page_translation.get_absolute_url())
    return HttpResponseNotFound("<h1>Page not found</h1>")


@require_POST
@permission_required("cms.change_page")
@json_response
# pylint: disable=unused-argument
def cancel_translation_process_ajax(
    request: HttpRequest, region_slug: str, language_slug: str, page_id: int
) -> JsonResponse:
    """
    This view is called for manually unsetting the translation process

    :param request: ajax request
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :param page_id: The id of the requested page
    :return: on success returns language of updated translation
    """
    region = request.region
    page = get_object_or_404(region.pages, id=page_id)
    if not (page_translation := page.get_translation(language_slug)):
        return JsonResponse(
            {
                "error": f"Page {page} does not have a translation for language '{language_slug}'"
            },
            status=404,
        )
    if settings.REDIS_CACHE:
        page_translation.all_versions.invalidated_update(currently_in_translation=False)
    else:
        page_translation.all_versions.update(currently_in_translation=False)
    # Get new (respectively old) translation state
    translation_state = page.get_translation_state(language_slug)
    return JsonResponse(
        {
            "success": f"Cancelled translation process for page {page} and language {page_translation.language}",
            "languageSlug": page_translation.language.slug,
            "translationState": translation_state,
        }
    )


@require_POST
@permission_required("cms.change_page")
def upload_xliff(
    request: HttpRequest, region_slug: str, language_slug: str
) -> HttpResponseRedirect:
    """
    Upload and import an XLIFF file

    :param request: The current request
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    """
    xliff_paths = []
    upload_files = request.FILES.getlist("xliff_file")
    xliff_dir_uuid = str(uuid.uuid4())
    if upload_files:
        logger.debug("Uploaded files: %r", upload_files)
        upload_dir = os.path.join(settings.XLIFF_UPLOAD_DIR, xliff_dir_uuid)
        os.makedirs(upload_dir, exist_ok=True)
        for upload_file in upload_files:
            # Check whether the file is valid
            if not upload_file.name.endswith((".zip", ".xliff", ".xlf")):
                # File type not supported
                messages.error(
                    request,
                    _('File "{}" is neither a ZIP archive nor an XLIFF file.').format(
                        upload_file.name
                    ),
                )
                logger.warning(
                    "%r tried to import the file %r which is neither a ZIP archive nor an XLIFF file",
                    request.user,
                    upload_file.name,
                )
                continue

            # Copy uploaded file from its temporary location into the upload directory
            with open(os.path.join(upload_dir, upload_file.name), "wb+") as file_write:
                # Using chunks() instead of read() ensures that large files don’t overwhelm your system’s memory
                for chunk in upload_file.chunks():
                    file_write.write(chunk)

            if upload_file.name.endswith(".zip"):
                # Extract zip archive
                xliff_paths_tmp, invalid_file_paths = extract_zip_archive(
                    os.path.join(upload_dir, upload_file.name), upload_dir
                )
                # Append contents of zip archive to total list of xliff files
                xliff_paths += xliff_paths_tmp
                if not xliff_paths_tmp:
                    messages.error(
                        request,
                        _('The ZIP archive "{}" does not contain XLIFF files.').format(
                            upload_file.name
                        ),
                    )
                elif invalid_file_paths:
                    messages.warning(
                        request,
                        _(
                            'The ZIP archive "{}" contains the following invalid files: "{}"'
                        ).format(upload_file.name, '", "'.join(invalid_file_paths)),
                    )
            else:
                # If file is an xliff file, directly append it to the paths
                xliff_paths.append(os.path.join(upload_dir, upload_file.name))
        # Check if at least one file was uploaded successfully
        if xliff_paths:
            logger.info(
                "XLIFF files %r uploaded into %r by %r",
                xliff_paths,
                upload_dir,
                request.user,
            )
            return redirect(
                "import_xliff",
                **{
                    "region_slug": region_slug,
                    "language_slug": language_slug,
                    "xliff_dir": xliff_dir_uuid,
                },
            )
    else:
        messages.error(
            request,
            _("No XLIFF file was selected for import."),
        )

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@permission_required("cms.change_page")
@transaction.atomic
def move_page(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    page_id: int,
    target_id: int,
    position: str,
) -> HttpResponseRedirect:
    """
    Move a page object in the page tree

    :param request: The current request
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :param page_id: The id of the page which should be moved
    :param target_id: The id of the page which determines the new position
    :param position: The new position of the page relative to the target (choices: :mod:`~integreat_cms.cms.constants.position`)
    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    """

    region = request.region
    page = get_object_or_404(region.pages, id=page_id)
    target = get_object_or_404(region.pages, id=target_id)

    try:
        page.move(target, position)
        # Call the save method on the (reloaded) node in order to trigger possible signal handlers etc.
        # (The move()-method executes raw sql which might cause problems if the instance isn't fetched again)
        page = Page.objects.get(id=page_id)
        page.save()
        logger.debug(
            "%r moved to %r of %r by %r",
            page,
            position,
            target,
            request.user,
        )
        messages.success(
            request,
            _('The page "{page}" was successfully moved.').format(
                page=page.best_translation.title
            ),
        )
    except (
        ValueError,
        InvalidPosition,
        InvalidMoveToDescendant,
        DBMutexTimeoutError,
        DBMutexError,
    ) as e:
        messages.error(request, e)
        logger.exception(e)

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@permission_required("cms.view_page")
# pylint: disable=unused-argument
def get_page_order_table_ajax(
    request: HttpRequest,
    region_slug: str,
    parent_id: int | None = None,
    page_id: int | None = None,
) -> HttpResponse:
    """
    Retrieve the order table for a given page and a given parent page.
    This is used in the page form to change the order of a page relative to its siblings.

    :param request: The current request
    :param region_slug: The slug of the current region
    :param parent_id: The id of the parent page to which the order table should be returned
    :param page_id: The id of the page of the current page form
    :return: The rendered page order table
    """

    region = request.region

    page = get_object_or_404(region.pages, id=page_id) if page_id else None

    if parent_id:
        parent = get_object_or_404(region.pages, id=parent_id)
        siblings = [
            sibling
            for sibling in parent.cached_children
            if not sibling.explicitly_archived
        ]
    else:
        siblings = region.get_root_pages().filter(explicitly_archived=False)

    logger.debug(
        "Page order table for page %r and siblings %r",
        page,
        siblings,
    )

    return render(
        request,
        "pages/_page_order_table.html",
        {
            "page": page,
            "siblings": siblings,
            "can_edit_page": request.user.has_perm("cms.change_page_object", page),
        },
    )


@permission_required("cms.view_page")
# pylint: disable=unused-argument
def render_mirrored_page_field(
    request: HttpRequest, region_slug: str, language_slug: str
) -> HttpResponse:
    """
    Retrieve the rendered mirrored page field template

    :param request: The current request
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: The rendered mirrored page field
    """
    # Get the region from which the content should be embedded
    region = get_object_or_404(Region, id=request.GET.get("region_id"))
    # Get the page in which the content should be embedded (to exclude it from the possible selections)
    page = Page.objects.filter(id=request.GET.get("page_id")).first()
    page_form = PageForm(
        data={"mirrored_page_region": region.id},
        instance=page,
        additional_instance_attributes={
            "region": region,
        },
    )
    # Pass language to mirrored page widget to render the preview urls
    page_form.fields["mirrored_page"].widget.language_slug = language_slug
    return render(
        request,
        "pages/_mirrored_page_field.html",
        {
            "page_form": page_form,
        },
    )


@require_POST
# pylint: disable=unused-argument
def refresh_date(
    request: HttpRequest,
    page_id: int,
    region_slug: str,
    language_slug: str,
) -> HttpResponseRedirect:
    """
    Refresh the date for up-to-date translations of a corresponding page

    :param request: The current request
    :param page_id: The id of the page of the current page form
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :raises ~django.core.exceptions.PermissionDenied: If the user does not have the permission to refresh page dates

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_form_view.PageFormView`
    """
    region = request.region
    page = get_object_or_404(region.get_pages(archived=False), id=page_id)

    if not request.user.has_perm("cms.change_page_object", page):
        raise PermissionDenied(
            f"{request.user!r} does not have the permission mark {page!r} as up-to-date"
        )

    # Consider only the last version of each translation
    page_translations = page.translations.filter(
        language__in=region.active_languages
    ).distinct("page__pk", "language__pk")
    # Sort page translations according to the position of their languages in the
    # language tree to ensure that the translations are not considered outdated.
    page_translations = sorted(
        page_translations,
        key=lambda page_translation: region.active_languages.index(
            page_translation.language
        ),
    )
    translations_to_update = [
        page_translation
        for page_translation in page_translations
        if page_translation.language.slug == language_slug
        or page_translation.is_up_to_date
    ]
    # Update timestamps of up-to-date translations
    for page_translation in translations_to_update:
        page_translation.save()

    messages.success(request, _("Marked all translations of this page as up-to-date"))
    return redirect(
        "edit_page",
        **{
            "page_id": page_id,
            "language_slug": language_slug,
            "region_slug": request.region.slug,
        },
    )
