"""
This module contains view actions related to pages.
"""
import json
import logging
import os
import uuid

from mptt.exceptions import InvalidMove

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from django.views.static import serve

from backend.settings import WEBAPP_URL
from ...decorators import region_permission_required, staff_required
from ...forms import PageForm
from ...models import Page, Language, Region, PageTranslation
from ...page_xliff_converter import PageXliffHelper, XLIFFS_DIR
from ...utils.pdf_utils import generate_pdf
from ...utils.slug_utils import generate_unique_slug

logger = logging.getLogger(__name__)


@login_required
@region_permission_required
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

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.edit_page", page):
        raise PermissionDenied

    page.explicitly_archived = True
    page.save()

    messages.success(request, _("Page was successfully archived"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
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

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.edit_page", page):
        raise PermissionDenied

    page.explicitly_archived = False
    page.save()

    if page.implicitly_archived:
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
    messages.success(request, _("Page was successfully restored."))
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.view_pages", raise_exception=True)
# pylint: disable=unused-argument
def view_page(request, page_id, region_slug, language_slug):
    """
    View page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be viewed
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pages/page_view.html"

    page_translation = page.get_translation(language_slug)
    mirrored_translation = page.get_mirrored_page_translation(language_slug)

    return render(
        request,
        template_name,
        {
            "page_translation": page_translation,
            "mirrored_translation": mirrored_translation,
            "mirrored_page_first": page.mirrored_page_first,
        },
    )


@login_required
@staff_required
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

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if page.children.exists():
        messages.error(request, _("You cannot delete a page which has subpages."))
    else:
        page.delete()
        messages.success(request, _("Page was successfully deleted"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
# pylint: disable=unused-argument
def export_pdf(request, region_slug, language_slug):
    """
    Function for handling a pdf export request for pages.
    The pages get extracted from request.GET attribute and the request is forwarded to :func:`~cms.utils.pdf_utils.generate_pdf`

    :param request: Request submitted for rendering pdf document
    :type request: ~django.http.HttpRequest

    :param region_slug: unique region slug
    :type region_slug: str

    :param language_slug: bcp47 slug of the current language
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: User login and permissions required

    :return: PDF document offered for download
    :rtype: ~django.http.HttpResponse
    """
    region = Region.get_current_region(request)
    # retrieve the selected page ids
    page_ids = request.POST.getlist("selected_ids[]")
    # collect the corresponding page objects
    pages = region.pages.filter(explicitly_archived=False, id__in=page_ids)
    # generate PDF document wrapped in a HtmlResponse object
    response = generate_pdf(region, language_slug, pages)
    # offer PDF document for download
    response["Content-Disposition"] = response["Content-Disposition"] + "; attachment"
    return response


def expand_page_translation_id(request, short_url_id):
    """
    Searches for a page translation with corresponding ID and redirects browser to web app

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param short_url_id: The id of the requested page
    :type short_url_id: int

    :return: A redirection to :class:`~backend.settings.WEBAPP_URL`
    :rtype: ~django.http.HttpResponseRedirect
    """

    page_translation = PageTranslation.objects.get(
        id=short_url_id
    ).latest_public_revision

    if page_translation and not page_translation.page.archived:
        return redirect(WEBAPP_URL + page_translation.get_absolute_url())
    return HttpResponseNotFound("<h1>Page not found</h1>")


@login_required
@region_permission_required
@permission_required("cms.view_pages", raise_exception=True)
def download_xliff(request, region_slug, language_slug):
    """
    Download a zip file of XLIFF files.
    The target languages and pages are selected and the source languages automatically determined.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the target language
    :type language_slug: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    page_ids = request.POST.getlist("selected_ids[]")

    if page_ids:
        region = Region.get_current_region(request)
        pages = get_list_or_404(region.pages, id__in=page_ids)
        target_language = get_object_or_404(
            region.language_tree_nodes, language__slug=language_slug
        ).language
        source_language = get_object_or_404(
            region.language_tree_nodes, language=target_language
        ).parent.language
        page_xliff_helper = PageXliffHelper(
            src_lang=source_language, tgt_lang=target_language
        )
        zip_path = page_xliff_helper.pages_to_zipped_xliffs(region, pages)
        if zip_path is not None and zip_path.startswith(XLIFFS_DIR):
            response = serve(
                request, zip_path.split(XLIFFS_DIR)[1], document_root=XLIFFS_DIR
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                zip_path.split(os.sep)[-1]
            )
            PageXliffHelper.post_translation_state(pages, target_language.slug, True)
            return response
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
# pylint: disable=unused-argument
def post_translation_state_ajax(request, region_slug):
    """This view is called for manually unseting the translation process

    :param request: ajax request
    :type request: ~django.http.HttpRequest
    :param region_slug: The slug of the current region
    :type region_slug: str
    :return: on success returns language of updated translation
    :rtype: ~django.http.JsonResponse
    """
    if request.method == "POST":
        decoded_json = json.loads(request.body.decode("utf-8"))
        target_language = decoded_json["language"]
        page_id = decoded_json["pageId"]
        translation_state = decoded_json["translationState"]
        region = Region.get_current_region(request)
        page = get_list_or_404(region.pages, id=page_id)
        PageXliffHelper.post_translation_state(
            list(page), target_language, translation_state
        )
        return JsonResponse({"language": target_language}, status=200)
    return JsonResponse(
        {"error": _("Could not update page translation state")}, status=400
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
def upload_xliff(request, region_slug, language_slug):
    """
    Upload and import an XLIFF file

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    if request.FILES.get("xliff_file"):
        xliff_helper = PageXliffHelper()
        upload_file = request.FILES["xliff_file"]
        upload_dir = os.path.join(XLIFFS_DIR, "upload", str(uuid.uuid4()))
        os.makedirs(upload_dir, exist_ok=True)
        with open(os.path.join(upload_dir, upload_file.name), "wb+") as file_write:
            for chunk in upload_file.chunks():
                file_write.write(chunk)
        if upload_file.name.endswith(".zip"):
            xliff_paths = xliff_helper.extract_zip_file(
                os.path.join(upload_dir, upload_file.name)
            )
        elif upload_file.name.endswith((".xliff", ".xlf")):
            xliff_paths = [os.path.join(upload_dir, upload_file.name)]
        else:  # no supported file name ending
            xliff_paths = []
        return render(
            request,
            "pages/page_xliff_confirm.html",
            {
                "upload_dir": os.path.basename(upload_dir),
                "translation_diffs": xliff_helper.generate_xliff_import_diff(
                    xliff_paths
                ),
                "language": Language.objects.get(slug=language_slug),
            },
        )
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
def confirm_xliff_import(request, region_slug, language_slug):
    """
    Confirm a started XLIFF import

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    if request.POST.get("upload_dir"):
        upload_dir = os.path.join(XLIFFS_DIR, "upload", request.POST.get("upload_dir"))
        xliff_paths = [
            os.path.join(upload_dir, f)
            for f in os.listdir(upload_dir)
            if os.path.isfile(os.path.join(upload_dir, f))
            and f.endswith((".xliff", ".xlf"))
        ]
        xliff_helper = PageXliffHelper()
        xliff_helper.import_xliff_files(xliff_paths, user=request.user)
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
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

    :param position: The new position of the page relative to the target (choices: :mod:`cms.constants.position`)
    :type position: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)
    target = get_object_or_404(region.pages, id=target_id)

    try:
        page.move_to(target, position)
        messages.success(
            request,
            _('The page "{page}" was successfully moved.').format(
                page=page.get_first_translation([language_slug]).title
            ),
        )
    except (ValueError, InvalidMove) as e:
        messages.error(request, e)
        logger.exception(e)

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
@permission_required("cms.grant_page_permissions", raise_exception=True)
# pylint: disable=too-many-branches
def grant_page_permission_ajax(request):
    """
    Grant a user editing or publishing permissions on a specific page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to grant page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = data.get("permission")
        page_id = data.get("page_id")
        user_id = data.get("user_id")

        logger.info(
            "Ajax call: The user %s wants to grant the permission to %s page with id %s to user with id %s.",
            request.user.username,
            permission,
            page_id,
            user_id,
        )

        page = Page.objects.get(id=page_id)
        user = get_user_model().objects.get(id=user_id)

        if not page.region.page_permissions_enabled:
            logger.info(
                'Error: Page permissions are not activated for the region "%s".',
                page.region,
            )
            raise PermissionDenied

        if not request.user.has_perm("cms.grant_page_permissions"):
            logger.info(
                "Error: The user %s does not have the permission to grant page permissions.",
                request.user.username,
            )
            raise PermissionDenied

        if not (request.user.is_superuser or request.user.is_staff):
            # additional checks if requesting user is no superuser or staff
            if page.region not in request.user.profile.regions:
                # requesting user can only grant permissions for pages of his region
                logger.info(
                    "Error: The user %s cannot grant permissions for region %s.",
                    request.user.username,
                    page.region.name,
                )
                raise PermissionDenied
            if page.region not in user.profile.regions:
                # user can only receive permissions for pages of his region
                logger.info(
                    "Error: The user %s cannot receive permissions for region %s.",
                    user.username,
                    page.region.name,
                )
                raise PermissionDenied

        if permission == "edit":
            # check, if the user already has this permission
            if user.has_perm("cms.edit_page", page):
                message = _(
                    "Information: The user {user} has this permission already."
                ).format(user=user.username)
                level_tag = "info"
            else:
                # else grant the permission by adding the user to the editors of the page
                page.editors.add(user)
                page.save()
                message = _("Success: The user {user} can now edit this page.").format(
                    user=user.username
                )
                level_tag = "success"
        elif permission == "publish":
            # check, if the user already has this permission
            if user.has_perm("cms.publish_page", page):
                message = _(
                    "Information: The user {user} has this permission already."
                ).format(user=user.username)
                level_tag = "info"
            else:
                # else grant the permission by adding the user to the publishers of the page
                page.publishers.add(user)
                page.save()
                message = _(
                    "Success: The user {user} can now publish this page."
                ).format(user=user.username)
                level_tag = "success"
        else:
            logger.info("Error: The permission %s is not supported.", permission)
            raise PermissionDenied
    # pylint: disable=broad-except
    except Exception as e:
        logger.error(e)
        message = _("An error has occurred. Please contact an administrator.")
        level_tag = "error"

    logger.info(message)

    return render(
        request,
        "pages/_page_permission_table.html",
        {
            "page": page,
            "page_form": PageForm(instance=page, region=page.region),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
@permission_required("cms.grant_page_permissions", raise_exception=True)
# pylint: disable=too-many-branches
def revoke_page_permission_ajax(request):
    """
    Remove a page permission for a given user and page

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to revoke page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = data.get("permission")
        page_id = data.get("page_id")
        page = Page.objects.get(id=page_id)
        user = get_user_model().objects.get(id=data.get("user_id"))

        logger.info(
            "Ajax call: The user %s wants to revoke the permission to %s page with id %s from user %s.",
            request.user.username,
            permission,
            page_id,
            user.username,
        )

        if not page.region.page_permissions_enabled:
            logger.info(
                'Error: Page permissions are not activated for the region "%s".',
                page.region,
            )
            raise PermissionDenied

        if not request.user.has_perm("cms.grant_page_permissions"):
            logger.info(
                "Error: The user %s does not have the permission to revoke page permissions.",
                request.user.username,
            )
            raise PermissionDenied

        if not (request.user.is_superuser or request.user.is_staff):
            # additional checks if requesting user is no superuser or staff
            if page.region not in request.user.profile.regions:
                # requesting user can only revoke permissions for pages of his region
                logger.info(
                    "Error: The user %s cannot revoke permissions for region %s.",
                    request.user.username,
                    page.region.name,
                )
                raise PermissionDenied

        if permission == "edit":
            if user in page.editors.all():
                # revoke the permission by removing the user to the editors of the page
                page.editors.remove(user)
                page.save()
            # check, if the user has this permission anyway
            if user.has_perm("cms.edit_page", page):
                message = _(
                    "Information: The user {user} has been removed from the editors of this page, "
                    "but has the implicit permission to edit this page anyway."
                ).format(user=user.username)
                level_tag = "info"
            else:
                message = _(
                    "Success: The user {user} cannot edit this page anymore."
                ).format(user=user.username)
                level_tag = "success"
        elif permission == "publish":
            if user in page.publishers.all():
                # revoke the permission by removing the user to the publishers of the page
                page.publishers.remove(user)
                page.save()
            # check, if the user already has this permission
            if user.has_perm("cms.publish_page", page):
                message = _(
                    "Information: The user {user} has been removed from the publishers of this page, "
                    "but has the implicit permission to publish this page anyway."
                ).format(user=user.username)
                level_tag = "info"
            else:
                message = _(
                    "Success: The user {user} cannot publish this page anymore."
                ).format(user=user.username)
                level_tag = "success"
        else:
            logger.info("Error: The permission %s is not supported.", permission)
            raise PermissionDenied
    # pylint: disable=broad-except
    except Exception as e:
        logger.error(e)
        message = _("An error has occurred. Please contact an administrator.")
        level_tag = "error"

    logger.info(message)

    return render(
        request,
        "pages/_page_permission_table.html",
        {
            "page": page,
            "page_form": PageForm(instance=page, region=page.region),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
# pylint: disable=unused-argument
def get_page_order_table_ajax(request, region_slug, page_id, parent_id):
    """
    Retrieve the order table for a given page and a given parent page.
    This is used in the page form to change the order of a page relative to its siblings.

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param page_id: The id of the page of the current page form
    :type page_id: int

    :param parent_id: The id of the parent page to which the order table should be returned
    :type parent_id: int

    :return: The rendered page order table
    :rtype: ~django.template.response.TemplateResponse
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if parent_id == "0":
        siblings = region.pages.filter(level=0)
    else:
        siblings = region.pages.filter(parent__id=parent_id)

    logger.debug(
        "Page order table for page %s and siblings %s",
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


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
# pylint: disable=unused-argument
def get_new_page_order_table_ajax(request, region_slug, parent_id):
    """
    Retrieve the order table for a new page and a given parent page.
    This is used in the page form to set the position of a new page relative to its siblings.

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param parent_id: The id of the parent page to which the order table should be returned
    :type parent_id: int

    :return: The rendered page order table
    :rtype: ~django.template.response.TemplateResponse
    """

    region = Region.get_current_region(request)

    if parent_id == "0":
        siblings = region.pages.filter(level=0)
    else:
        siblings = region.pages.filter(parent__id=parent_id)

    logger.debug(
        "Page order table for a new page and siblings %s",
        siblings,
    )

    return render(
        request,
        "pages/_page_order_table.html",
        {
            "siblings": siblings,
        },
    )


@login_required
def render_mirrored_page_field(request):
    """
    Retrieve the rendered mirrored page field template

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :return: The rendered mirrored page field
    :rtype: ~django.template.response.TemplateResponse
    """
    # Get the region from which the content should be embedded
    region = get_object_or_404(Region, id=request.GET.get("region_id"))
    # Get the page in which the content should be embedded (to exclude it from the possible selections)
    page = Page.objects.filter(id=request.GET.get("page_id")).first()
    page_form = PageForm(
        {"mirrored_page_region": region.id},
        instance=page,
        region=region,
    )
    return render(
        request,
        "pages/_mirrored_page_field.html",
        {
            "page_form": page_form,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
# pylint: disable=unused-argument
def slugify_ajax(request, region_slug, language_slug):
    """checks the current user input for page title and generates unique slug for permalink

    :param request: The current request
    :type request: ~django.http.HttpResponse
    :param region_slug: region identifier
    :type region_slug: str
    :param language_slug: language slug
    :type language_slug: str
    :return: unique page translation slug
    :rtype: str
    """
    json_data = json.loads(request.body)
    form_title = slugify(json_data["title"], allow_unicode=True)
    region = Region.get_current_region(request)
    language = get_object_or_404(region.languages, slug=language_slug)
    page = region.pages.filter(id=request.GET.get("page")).first()
    page_translation = PageTranslation.objects.filter(
        page=page,
        language=language,
    ).first()
    kwargs = {
        "slug": form_title,
        "manager": PageTranslation.objects,
        "object_instance": page_translation,
        "foreign_model": "page",
        "region": region,
        "language": language,
    }
    unique_slug = generate_unique_slug(**kwargs)
    return JsonResponse({"unique_slug": unique_slug})
