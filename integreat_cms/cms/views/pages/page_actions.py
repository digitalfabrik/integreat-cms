"""
This module contains view actions related to pages.
"""
import json
import logging
import os
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.db import transaction

from treebeard.exceptions import InvalidPosition, InvalidMoveToDescendant

from ....api.decorators import json_response
from ...constants import text_directions
from ...decorators import permission_required
from ...forms import PageForm
from ...models import Page, Region, PageTranslation
from ...utils.file_utils import extract_zip_archive

logger = logging.getLogger(__name__)


@require_POST
def archive_page(request, page_id, region_slug, language_slug):
    """
    Archive page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be archived
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = request.region
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.change_page_object", page):
        raise PermissionDenied(
            f"{request.user!r} does not have the permission to archive {page!r}"
        )

    page.explicitly_archived = True
    page.save()

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
def restore_page(request, page_id, region_slug, language_slug):
    """
    Restore page object (set ``archived=False``)

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be restored
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = request.region
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.change_page_object", page):
        raise PermissionDenied(
            f"{request.user!r} does not have the permission to restore {page!r}"
        )

    page.explicitly_archived = False
    page.save()

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
def preview_page_ajax(request, page_id, region_slug, language_slug):
    """
    Preview page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be viewed
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :raises ~django.http.Http404: HTTP status 404 if page translation does not exist

    :return: Significant page data as a JSON.
    :rtype: ~django.http.JsonResponse
    """
    region = request.region
    page = get_object_or_404(region.pages, id=page_id)

    page_translation = page.get_translation(language_slug)
    if not page_translation:
        raise Http404("Translation of the given page could not be found")
    mirrored_translation = page.get_mirrored_page_translation(language_slug)

    return JsonResponse(
        data={
            "title": page_translation.title,
            "page_translation": page_translation.content,
            "mirrored_translation": mirrored_translation.content
            if mirrored_translation
            else "",
            "mirrored_page_first": page.mirrored_page_first,
            "right_to_left": page_translation.language.text_direction
            == text_directions.RIGHT_TO_LEFT
            if page_translation
            else False,
        }
    )


@permission_required("cms.view_page")
@json_response
# pylint: disable=unused-argument
def get_page_content_ajax(request, region_slug, language_slug, page_id):
    """
    Get content of a page translation based on language slug

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :param page_id: The id of the page which should be viewed
    :type page_id: int

    :raises ~django.http.Http404: HTTP status 404 if page translation does not exist

    :return: Page translation content as a JSON.
    :rtype: ~django.http.JsonResponse
    """
    region = request.region
    page = get_object_or_404(region.pages, id=page_id)
    page_translation = page.get_translation(language_slug)
    if not page_translation:
        raise Http404("Translation of the given page could not be found")
    return JsonResponse(data={"content": page_translation.content})


@require_POST
@permission_required("cms.delete_page")
@transaction.atomic
def delete_page(request, page_id, region_slug, language_slug):
    """
    Delete page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be deleted
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
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


def expand_page_translation_id(request, short_url_id):
    """
    Searches for a page translation with corresponding ID and redirects browser to web app

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param short_url_id: The id of the requested page
    :type short_url_id: int

    :return: A redirection to :class:`~integreat_cms.core.settings.WEBAPP_URL`
    :rtype: ~django.http.HttpResponseRedirect
    """

    page_translation = PageTranslation.objects.get(id=short_url_id).public_version

    if page_translation and not page_translation.page.archived:
        return redirect(settings.WEBAPP_URL + page_translation.get_absolute_url())
    return HttpResponseNotFound("<h1>Page not found</h1>")


@require_POST
@permission_required("cms.change_page")
@json_response
# pylint: disable=unused-argument
def cancel_translation_process_ajax(request, region_slug, language_slug, page_id):
    """
    This view is called for manually unsetting the translation process

    :param request: ajax request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :param page_id: The id of the requested page
    :type page_id: int

    :return: on success returns language of updated translation
    :rtype: ~django.http.JsonResponse
    """
    region = request.region
    page = get_object_or_404(region.pages, id=page_id)
    page_translation = page.get_translation(language_slug)
    if not page_translation:
        return JsonResponse(
            {
                "error": f"Page {page} does not have a translation for language '{language_slug}'"
            },
            status=404,
        )
    page_translation.currently_in_translation = False
    page_translation.save()
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
def upload_xliff(request, region_slug, language_slug):
    """
    Upload and import an XLIFF file

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
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
# pylint: disable=too-many-arguments
def move_page(request, region_slug, language_slug, page_id, target_id, position):
    """
    Move a page object in the page tree

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :param page_id: The id of the page which should be moved
    :type page_id: int

    :param target_id: The id of the page which determines the new position
    :type target_id: int

    :param position: The new position of the page relative to the target (choices: :mod:`~integreat_cms.cms.constants.position`)
    :type position: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
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
    except (ValueError, InvalidPosition, InvalidMoveToDescendant) as e:
        messages.error(request, e)
        logger.exception(e)

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@permission_required("cms.change_page")
@permission_required("cms.grant_page_permissions")
# pylint: disable=too-many-branches,unused-argument
def grant_page_permission_ajax(request, region_slug):
    """
    Grant a user editing or publishing permissions on a specific page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to grant page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = data.get("permission")
        page = Page.objects.get(id=data.get("page_id"))
        user = get_user_model().objects.get(id=data.get("user_id"))

        logger.debug(
            "[AJAX] %r wants to grant %r the permission to %s %r",
            request.user,
            user,
            permission,
            page,
        )

        if not page.region.page_permissions_enabled:
            raise PermissionDenied(
                f"Page permissions are not activated for {page.region!r}"
            )

        if not (request.user.is_superuser or request.user.is_staff):
            # additional checks if requesting user is no superuser or staff
            if page.region not in request.user.regions:
                # requesting user can only grant permissions for pages of his region
                logger.warning(
                    "Error: %r cannot grant permissions for %r",
                    request.user,
                    page.region,
                )
                raise PermissionDenied
            if page.region not in user.regions:
                # user can only receive permissions for pages of his region
                logger.warning(
                    "Error: %r cannot receive permissions for %r",
                    user,
                    page.region,
                )
                raise PermissionDenied

        if permission == "edit":
            # check, if the user already has this permission
            if user.has_perm("cms.change_page_object", page):
                message = _(
                    'Information: The user "{}" has this permission already.'
                ).format(user.full_user_name)
                level_tag = "info"
            else:
                # else grant the permission by adding the user to the editors of the page
                page.editors.add(user)
                page.save()
                message = _('Success: The user "{}" can now edit this page.').format(
                    user.full_user_name
                )
                level_tag = "success"
        elif permission == "publish":
            # check, if the user already has this permission
            if user.has_perm("cms.publish_page_object", page):
                message = _(
                    'Information: The user "{}" has this permission already.'
                ).format(user.full_user_name)
                level_tag = "info"
            else:
                # else grant the permission by adding the user to the publishers of the page
                page.publishers.add(user)
                page.save()
                message = _('Success: The user "{}" can now publish this page.').format(
                    user.full_user_name
                )
                level_tag = "success"
        else:
            logger.warning("Error: The permission %r is not supported", permission)
            raise PermissionDenied
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception(e)
        message = _("An error has occurred. Please contact an administrator.")
        level_tag = "error"

    logger.debug(message)

    return render(
        request,
        "pages/_page_permission_table.html",
        {
            "page": page,
            "page_form": PageForm(
                instance=page,
                additional_instance_attributes={
                    "region": page.region,
                },
            ),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@require_POST
@permission_required("cms.change_page")
@permission_required("cms.grant_page_permissions")
# pylint: disable=too-many-branches,unused-argument
def revoke_page_permission_ajax(request, region_slug):
    """
    Remove a page permission for a given user and page

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to revoke page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = data.get("permission")
        page = Page.objects.get(id=data.get("page_id"))
        user = get_user_model().objects.get(id=data.get("user_id"))

        logger.debug(
            "[AJAX] %r wants to revoke the permission to %s %r from %r",
            request.user,
            permission,
            page,
            user,
        )

        if not page.region.page_permissions_enabled:
            raise PermissionDenied(
                f"Page permissions are not activated for {page.region!r}"
            )

        if not (request.user.is_superuser or request.user.is_staff):
            # additional checks if requesting user is no superuser or staff
            if page.region not in request.user.regions:
                # requesting user can only revoke permissions for pages of his region
                logger.warning(
                    "Error: %r cannot revoke permissions for %r",
                    request.user,
                    page.region,
                )
                raise PermissionDenied

        if permission == "edit":
            if user in page.editors.all():
                # revoke the permission by removing the user to the editors of the page
                page.editors.remove(user)
                page.save()
            # check, if the user has this permission anyway
            if user.has_perm("cms.change_page_object", page):
                message = _(
                    'Information: The user "{}" has been removed from the editors of this page, '
                    "but has the implicit permission to edit this page anyway."
                ).format(user.full_user_name)
                level_tag = "info"
            else:
                message = _(
                    'Success: The user "{}" cannot edit this page anymore.'
                ).format(user.full_user_name)
                level_tag = "success"
        elif permission == "publish":
            if user in page.publishers.all():
                # revoke the permission by removing the user to the publishers of the page
                page.publishers.remove(user)
                page.save()
            # check, if the user already has this permission
            if user.has_perm("cms.publish_page_object", page):
                message = _(
                    'Information: The user "{}" has been removed from the publishers of this page, '
                    "but has the implicit permission to publish this page anyway."
                ).format(user.full_user_name)
                level_tag = "info"
            else:
                message = _(
                    'Success: The user "{}" cannot publish this page anymore.'
                ).format(user.full_user_name)
                level_tag = "success"
        else:
            logger.warning("Error: The permission %r is not supported", permission)
            raise PermissionDenied
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception(e)
        message = _("An error has occurred. Please contact an administrator.")
        level_tag = "error"

    logger.debug(message)

    return render(
        request,
        "pages/_page_permission_table.html",
        {
            "page": page,
            "page_form": PageForm(
                instance=page,
                additional_instance_attributes={
                    "region": page.region,
                },
            ),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@permission_required("cms.view_page")
# pylint: disable=unused-argument
def get_page_order_table_ajax(request, region_slug, parent_id=None, page_id=None):
    """
    Retrieve the order table for a given page and a given parent page.
    This is used in the page form to change the order of a page relative to its siblings.

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param parent_id: The id of the parent page to which the order table should be returned
    :type parent_id: int

    :param page_id: The id of the page of the current page form
    :type page_id: int

    :return: The rendered page order table
    :rtype: ~django.template.response.TemplateResponse
    """

    region = request.region

    if page_id:
        page = get_object_or_404(region.pages, id=page_id)
    else:
        page = None

    if parent_id or page:
        parent = (
            get_object_or_404(region.pages, id=parent_id) if parent_id else page.parent
        )
        siblings = parent.cached_children
    else:
        siblings = region.get_root_pages()

    siblings = [sibling for sibling in siblings if not sibling.explicitly_archived]

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
        },
    )


@permission_required("cms.view_page")
# pylint: disable=unused-argument
def render_mirrored_page_field(request, region_slug, language_slug):
    """
    Retrieve the rendered mirrored page field template

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: The rendered mirrored page field
    :rtype: ~django.template.response.TemplateResponse
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
