"""
This module contains view actions for media related objects.
"""
import logging

from django.db.models import Q, ProtectedError
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ....api.decorators import json_response
from ...decorators import permission_required

from ...forms import (
    UploadMediaFileForm,
    ReplaceMediaFileForm,
    MediaFileForm,
    MediaMoveForm,
    CreateDirectoryForm,
    DirectoryForm,
)
from ...models import MediaFile, Directory

logger = logging.getLogger(__name__)


@permission_required("cms.view_directory")
@permission_required("cms.view_mediafile")
@json_response
# pylint: disable=unused-argument
def get_directory_path_ajax(request, region_slug=None):
    """
    View provides the frontend with the current directory path for the breadcrumbs.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    directory_path = []

    if request.GET.get("directory"):
        directory = get_object_or_404(
            Directory.objects.filter(Q(region=region) | Q(region__isnull=True)),
            id=request.GET.get("directory"),
        )

        while directory:
            directory_path.insert(0, directory.serialize())
            directory = directory.parent

    return JsonResponse({"data": directory_path})


@permission_required("cms.view_directory")
@permission_required("cms.view_mediafile")
@json_response
# pylint: disable=unused-argument
def get_directory_content_ajax(request, region_slug=None):
    """
    View provides the frontend with the content of a directory via AJAX.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    directory = None
    if request.GET.get("directory"):
        directory = get_object_or_404(
            Directory.objects.filter(Q(region=region) | Q(region__isnull=True)),
            id=request.GET.get("directory"),
        )

    media_files = MediaFile.objects.filter(
        Q(region=region) | Q(region__isnull=True), Q(parent_directory=directory)
    )
    directories = Directory.objects.filter(
        Q(region=region) | Q(region__isnull=True), parent=directory
    )

    result = list(map(lambda d: d.serialize(), list(directories) + list(media_files)))

    return JsonResponse({"data": result})


@json_response
@permission_required("cms.view_directory")
@permission_required("cms.view_mediafile")
# pylint: disable=unused-argument
def get_query_search_results_ajax(request, region_slug=None):
    """
    View to search the media library

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response with the search result
    :rtype: ~django.http.JsonResponse
    """
    query = request.GET.get("query")
    logger.debug("Media library searched with query %r", query)
    region = request.region

    media_files = MediaFile.search(region, query)
    directories = Directory.search(region, query)
    result = list(map(lambda d: d.serialize(), list(directories) + list(media_files)))

    logger.debug("Media library search results: %r", result)
    return JsonResponse({"data": result})


@require_POST
@permission_required("cms.upload_mediafile")
@json_response
# pylint: disable=unused-argument
def upload_file_ajax(request, region_slug=None):
    """
    View to create a file via an AJAX upload.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    media_file_form = UploadMediaFileForm(data=request.POST, files=request.FILES)

    # Set region so it can be checked whether it's the same like the parent directory
    media_file_form.instance.region = region

    if not media_file_form.is_valid():
        return HttpResponse(
            ". ".join(
                message["text"] for message in media_file_form.get_error_messages()
            ),
            status=400,
        )

    # Save form
    media_file = media_file_form.save()

    return JsonResponse(
        {
            "messages": [
                {
                    "type": "success",
                    "text": _('File "{}" was uploaded successfully').format(
                        media_file.name
                    ),
                }
            ],
            "file": media_file.serialize(),
        }
    )


@require_POST
@permission_required("cms.change_mediafile")
@json_response
# pylint: disable=unused-argument
def edit_file_ajax(request, region_slug=None):
    """
    View provides the edit of a file via AJAX.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    media_file = get_object_or_404(
        MediaFile.objects.filter(region=region), id=request.POST.get("id")
    )

    media_file_form = MediaFileForm(data=request.POST, instance=media_file)

    if not media_file_form.is_valid():
        return JsonResponse(
            {
                "messages": media_file_form.get_error_messages(),
            },
            status=400,
        )

    if not media_file_form.has_changed():
        return JsonResponse(
            {
                "messages": [
                    {
                        "type": "info",
                        "text": _("No changes detected"),
                    }
                ],
                "file": media_file.serialize(),
            }
        )

    # Save form
    media_file_form.save()

    return JsonResponse(
        {
            "messages": [
                {
                    "type": "success",
                    "text": _('File "{}" was saved successfully').format(
                        media_file.name
                    ),
                }
            ],
            "file": media_file.serialize(),
        }
    )


@require_POST
@permission_required("cms.replace_mediafile")
@json_response
# pylint: disable=unused-argument
def replace_file_ajax(request, region_slug=None):
    """
    View provides the replacement of a file via AJAX.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    media_file = get_object_or_404(
        MediaFile.objects.filter(region=region), id=request.POST.get("id")
    )

    media_file_form = ReplaceMediaFileForm(
        data=request.POST, instance=media_file, files=request.FILES
    )

    if not media_file_form.is_valid():
        return JsonResponse(
            {
                "messages": media_file_form.get_error_messages(),
            },
            status=400,
        )

    # Save form
    media_file_form.save()
    logger.info("%r was replaced by %r", media_file, request.user)

    return JsonResponse(
        {
            "messages": [
                {
                    "type": "success",
                    "text": _('File "{}" was saved successfully').format(
                        media_file.name
                    ),
                }
            ],
            "file": media_file.serialize(),
        }
    )


@require_POST
@permission_required("cms.delete_mediafile")
@json_response
# pylint: disable=unused-argument
def delete_file_ajax(request, region_slug=None):
    """
    View to delete a file via an AJAX call.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    media_file = get_object_or_404(
        MediaFile.objects.filter(region=region), id=request.POST.get("id")
    )

    # Delete corresponding physical files
    media_file.file.delete()
    media_file.thumbnail.delete()
    # Delete database entry
    media_file.delete()

    return JsonResponse(
        {
            "messages": [
                {
                    "type": "success",
                    "text": _('File "{}" was successfully deleted').format(
                        media_file.name
                    ),
                }
            ],
            "file": media_file.serialize(),
        }
    )


@require_POST
@permission_required("cms.add_directory")
@json_response
# pylint: disable=unused-argument
def create_directory_ajax(request, region_slug=None):
    """
    View provides the frontend with the option to create a directory via AJAX.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    directory_form = CreateDirectoryForm(data=request.POST)

    # Set region so it can be checked whether it's the same like the parent directory
    directory_form.instance.region = region

    if not directory_form.is_valid():
        return JsonResponse(
            {
                "messages": directory_form.get_error_messages(),
            },
            status=400,
        )

    # Save form
    directory = directory_form.save()

    return JsonResponse(
        {
            "messages": [
                {
                    "type": "success",
                    "text": _('Directory "{}" was created successfully').format(
                        directory.name
                    ),
                }
            ],
            "directory": directory.serialize(),
        }
    )


@require_POST
@permission_required("cms.change_directory")
@json_response
# pylint: disable=unused-argument
def edit_directory_ajax(request, region_slug=None):
    """
    View provides the frontend with the option to modify a directory via AJAX.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    directory = get_object_or_404(
        Directory.objects.filter(region=region), id=request.POST.get("id")
    )

    directory_form = DirectoryForm(data=request.POST, instance=directory)

    if not directory_form.is_valid():
        return JsonResponse(
            {
                "messages": directory_form.get_error_messages(),
            },
            status=400,
        )

    if not directory_form.has_changed():
        return JsonResponse(
            {
                "messages": [{"type": "info", "text": _("No changes detected")}],
                "directory": directory.serialize(),
            }
        )

    # Save form
    directory = directory_form.save()

    return JsonResponse(
        {
            "messages": [
                {
                    "type": "success",
                    "text": _('Directory "{}" was saved successfully').format(
                        directory.name
                    ),
                }
            ],
            "directory": directory.serialize(),
        }
    )


@require_POST
@permission_required("cms.delete_directory")
@json_response
# pylint: disable=unused-argument
def delete_directory_ajax(request, region_slug=None):
    """
    View provides the frontend with the option to delete a directory via AJAX.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = request.region

    directory = get_object_or_404(
        Directory.objects.filter(region=region), id=request.POST.get("id")
    )

    try:
        directory.delete()
    except ProtectedError:
        return JsonResponse(
            {
                "messages": [
                    {
                        "type": "warning",
                        "text": _(
                            'Directory "{}" cannot be deleted because it is not empty'
                        ).format(directory.name),
                    }
                ],
            },
            status=400,
        )

    return JsonResponse(
        {
            "messages": [
                {
                    "type": "success",
                    "text": _('Directory "{}" was successfully deleted').format(
                        directory.name
                    ),
                }
            ],
            "directory": directory.serialize(),
        }
    )


@require_POST
@permission_required("cms.change_directory")
@permission_required("cms.change_mediafile")
@json_response
# pylint: disable=unused-argument
def move_file_ajax(request, region_slug=None):
    """
    This view provides the frontend with the option to move files via AJAX.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """

    region = request.region

    media_file = get_object_or_404(
        MediaFile.objects.filter(region=region), id=request.POST.get("mediafile_id")
    )

    media_move_form = MediaMoveForm(data=request.POST, instance=media_file)

    if not media_move_form.is_valid():
        return JsonResponse(
            {
                "messages": media_move_form.get_error_messages(),
            },
            status=400,
        )

    if not media_move_form.has_changed():
        return JsonResponse(
            {
                "messages": [{"type": "info", "text": _("No changes detected")}],
            }
        )

    # Save form
    media_file = media_move_form.save()

    return JsonResponse(
        {
            "messages": [
                {
                    "type": "success",
                    "text": _(
                        'File "{}" was moved successfully into directory "{}"'
                    ).format(media_file.name, media_file.parent_directory or "Home"),
                }
            ],
        }
    )
