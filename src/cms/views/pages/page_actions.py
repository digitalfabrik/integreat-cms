"""

Returns:
    [type]: [description]
"""
import hashlib
import json
import logging
import os
import uuid
<<<<<<< HEAD
=======
import pyperclip
>>>>>>> added comments and bundled pdf styling in css file

from mptt.exceptions import InvalidMove

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.utils.translation import ugettext as _
from django.views.static import serve
from django.http import HttpResponseNotFound
from django.template.loader import get_template

from xhtml2pdf import pisa

from backend.settings import WEBAPP_URL
from ...decorators import region_permission_required, staff_required
from ...forms.pages import PageForm
from ...models import Page, Language, Region, PageTranslation
from ...page_xliff_converter import PageXliffHelper, XLIFFS_DIR

logger = logging.getLogger(__name__)


@login_required
@region_permission_required
def archive_page(request, page_id, region_slug, language_code):
    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.edit_page", page):
        raise PermissionDenied

    page.archived = True
    page.save()

    messages.success(request, _("Page was successfully archived"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_code": language_code,
        },
    )


@login_required
@region_permission_required
def restore_page(request, page_id, region_slug, language_code):
    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.edit_page", page):
        raise PermissionDenied

    page.archived = False
    page.save()

    messages.success(request, _("Page was successfully restored"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_code": language_code,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.view_pages", raise_exception=True)
# pylint: disable=unused-argument
def view_page(request, page_id, region_slug, language_code):
    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    template_name = "pages/page_view.html"

    page_translation = page.get_translation(language_code)

    return render(request, template_name, {"page_translation": page_translation})


@login_required
@staff_required
def delete_page(request, page_id, region_slug, language_code):
    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if page.children.exists():
        messages.error(request, _("You cannot delete a page which has children"))
    else:
        page.delete()
        messages.success(request, _("Page was successfully deleted"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_code": language_code,
        },
    )


<<<<<<< HEAD
<<<<<<< HEAD
def expand_short_url(request, short_url_id):
=======
""" def export_pdf(request, page_id, region_slug, language_code):
    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, pk=page_id)
    page_translation = page.get_translation(language_code)
    # create file-like buffer to receive pdf data
    buffer = io.BytesIO()
    
    print(page_translation.text)
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=72, 
        leftMargin=72, 
        topMargin=72, 
        bottomMargin=18
    )
    Story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    header = '<font size="8">%s</font>' % page_translation.title
    styles.add(ParagraphStyle(
        'IntegreatHeader',
        fontName='Courier-Bold',
        alignment=TA_JUSTIFY
    ))
    Story.append(Paragraph(header, styles["IntegreatHeader"]))
    Story.append(Spacer(1, 12))
    paragraph = '<font size="12">%s</font>' % page_translation.text
    # paragraph = page_translation.text
    styles.add(ParagraphStyle(
        'integreat-text',
        fontName='Courier',
        alignment=TA_JUSTIFY
    ))
    Story.append(Paragraph(paragraph, styles["Normal"]))
    doc.build(Story)

    # FileResponse sets content-disposition header 
    # so that browser offers to save to save the file
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='hello.pdf') """


"""
To allow URL references to be resolved using Django's STATIC_URL,
specify a link_callback parameter to point to function that 
converts relative to absolute URLs 
"""


=======
# pylint: disable=unused-argument
>>>>>>> added comments and bundled pdf styling in css file
def link_callback(uri, rel):
    """
    according to xhtml2pdf documentation this function is neccessary for
    resolving the django static files references and returning absolute paths
    to the files

    :param uri: uri that is generated by django template tag 'static'
    :type uri: str
    :return: the absolute path according to django's static file settings
    :rtype: str
    """
    sUrl = settings.STATIC_URL
    sRoot = settings.STATIC_ROOT
    mUrl = settings.MEDIA_URL
    mRoot = settings.MEDIA_ROOT
    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri
    # make sure that file exists
    if not os.path.isfile(path):
        raise Exception(
            "media URI must start with %s or %s, but received uri was %s"
            % (sUrl, mUrl, uri)
        )
    return path


@login_required
@region_permission_required
# pylint: disable=unused-argument
def export_pdf(request, region_slug, language_code):
    """
    function for handling a pdf export request for a single page
    if the page is a root page the corresponding django template
    inserts the content of all children pages

    :param request: request submitted for rendering pdf document
    :type request: ~django.http.HttpRequest
    :param language_code: bcp47 code of the current language
    :type language_code: str
    :raises PermissionDenied: user login and permissions required
    :return: pdf document offered for download
    :rtype: ~django.http.HttpRequest
    """
    page_ids = []
    region = Region.get_current_region(request)
    for page_id in request.GET.get('pages').split(','):
        page_ids.append(page_id)
    # retrieve all selected pages
    pages = region.pages.filter(archived=False, id__in=page_ids)
    amount_pages = len(pages)
    pdf_key_list = [region_slug]
    for page in pages:
        # retrieve the translation for each page
        page_translation = page.get_translation(language_code)
        pdf_key_list.append(page_translation.id)
        pdf_key_list.append(page_translation.last_updated)
    pdf_key_string = '_'.join(map(str, pdf_key_list))
    pdf_hash_key = hashlib.sha256(bytes(pdf_key_string, 'utf-8')).hexdigest()
    cached_response = cache.get(pdf_hash_key, 'has_expired')
    if (cached_response is not 'has_expired'):
        return cached_response
    else:
        language = Language.objects.get(code=language_code)
        template_path = "pages/page_view.html"
        context = {
            "html2pdf": True,
            "region": region,
            "pages": pages,
            "language": language,
            "amount_pages": amount_pages
        }
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            "attachment; filename=%s.pdf" % page_translation.title
        )
        template = get_template(template_path)
        html = template.render(context)
        pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
        if pisa_status.err:
            return HttpResponse(
                "There was an error while rendering the following html <pre>"
                + html
                + "</pre>"
            )
        cache.set(pdf_hash_key, response, 60*60*24)
        return response


@login_required
def copy_short_url(request, page_id, region_slug, language_code):
>>>>>>> installed xhtml2pdf: html content of page editor
    """
    Searches for a page with requested short_url_id and redirects to that page.
    """
    queryset = PageTranslation.objects.filter(short_url_id=short_url_id)
    page_translation = queryset.first().latest_public_revision

    if page_translation and not page_translation.page.archived:
        return redirect(WEBAPP_URL + page_translation.get_absolute_url())
    return HttpResponseNotFound("<h1>Page not found</h1>")


def expand_page_translation_id(request, short_url_id):
    """
    Searches for a page translation with corresponding ID and redirects browser to web app
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
def download_xliff(request, region_slug, language_code):
    """
    Create zip file that contains XLIFF files for target language.
    """
    page_ids = []
    for page_id in request.GET.get("pages").split(","):
        if page_id.isnumeric():
            page_ids.append(int(page_id))
    if page_ids:
        region = Region.get_current_region(request)
        pages = get_list_or_404(region.pages, id__in=page_ids)
        target_language = get_object_or_404(
            region.language_tree_nodes, language__code=request.GET.get("target_lang")
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
            return response
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_code": language_code,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
def upload_xliff(request, region_slug, language_code):
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
                "language": Language.objects.get(code=language_code),
            },
        )
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_code": language_code,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
def confirm_xliff_import(request, region_slug, language_code):
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
            "language_code": language_code,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
# pylint: disable=too-many-arguments
def move_page(request, region_slug, language_code, page_id, target_id, position):
    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)
    target = get_object_or_404(region.pages, id=target_id)

    try:
        page.move_to(target, position)
        messages.success(
            request,
            _('The page "{page}" was successfully moved.').format(
                page=page.get_first_translation([language_code]).title
            ),
        )
    except (ValueError, InvalidMove) as e:
        messages.error(request, e)
        logger.exception(e)

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_code": language_code,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
@permission_required("cms.grant_page_permissions", raise_exception=True)
# pylint: disable=too-many-branches
def grant_page_permission_ajax(request):

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
            "page_form": PageForm(instance=page),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
@permission_required("cms.grant_page_permissions", raise_exception=True)
# pylint: disable=too-many-branches
def revoke_page_permission_ajax(request):

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
            "page_form": PageForm(instance=page),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
# pylint: disable=unused-argument
def get_page_order_table_ajax(request, region_slug, page_id, parent_id):

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
def get_pages_list_ajax(request):
    decoded_json = json.loads(request.body.decode("utf-8"))
    if "region" not in decoded_json or decoded_json["region"] == "":
        page = Page.objects.get(id=decoded_json["current_page"])

        if not request.user.has_perm("cms.edit_page", page):
            logger.info(
                "Error: The user %s cannot edit page %s.",
                request.user.username,
                page,
            )
            raise PermissionDenied

        page.mirrored_page = None
        page.save()
        return JsonResponse({"nolist": True})
    region = get_object_or_404(Region, id=decoded_json["region"])
    result = []
    for page in region.pages.all():
        result.append(
            {
                "id": page.id,
                "name": " -> ".join(
                    [
                        page_iter.best_language_title()
                        for page_iter in page.get_ancestors(include_self=True)
                    ]
                ),
            }
        )
    result = sorted(result, key=lambda k: k["name"])
    return JsonResponse(result, safe=False)


@login_required
def save_mirrored_page(request):
    decoded_json = json.loads(request.body.decode("utf-8"))
    page = Page.objects.get(id=decoded_json["current_page"])

    if not request.user.has_perm("cms.edit_page", page):
        logger.info(
            "Error: The user %s cannot edit page %s.",
            request.user.username,
            page,
        )
        raise PermissionDenied

    if int(decoded_json["mirrored_page"]) == 0:
        page.mirrored_page = None
    else:
        page.mirrored_page = Page.objects.get(id=int(decoded_json["mirrored_page"]))
        page.mirrored_page_first = decoded_json["mirrored_page_first"] == "True"
    page.save()
    return JsonResponse({"code": True})
