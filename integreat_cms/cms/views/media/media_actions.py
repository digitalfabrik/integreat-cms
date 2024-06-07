"""
This module contains view actions for media related objects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.db.models import ProtectedError, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ....api.decorators import json_response
from ...decorators import permission_required
from ...forms import (
    CreateDirectoryForm,
    DirectoryForm,
    MediaFileForm,
    MediaMoveForm,
    ReplaceMediaFileForm,
    UploadMediaFileForm,
)
from ...models import Directory, MediaFile

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

logger = logging.getLogger(__name__)


@permission_required("cms.view_directory")
@permission_required("cms.view_mediafile")
@json_response
# pylint: disable=unused-argument
def get_directory_path_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View provides the frontend with the current directory path for the breadcrumbs.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
    """
    region = request.region

    directory_path: list[dict[str, Any]] = []

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
def get_directory_content_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View provides the frontend with the content of a directory via AJAX.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
    """
    region = request.region

    directory = None
    if request.GET.get("directory"):
        directory = get_object_or_404(
            Directory.objects.filter(
                Q(region=region) | Q(region__isnull=True, is_hidden=False),
            ),
            id=request.GET.get("directory"),
        )

    media_files = MediaFile.objects.filter(
        Q(region=region) | Q(region__isnull=True, is_hidden=False),
        Q(parent_directory=directory),
    )
    directories = Directory.objects.filter(
        Q(region=region) | Q(region__isnull=True, is_hidden=False), parent=directory
    )

    result = [d.serialize() for d in list(directories) + list(media_files)]

    return JsonResponse({"data": result})


@json_response
@permission_required("cms.view_directory")
@permission_required("cms.view_mediafile")
# pylint: disable=unused-argument
def get_query_search_results_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View to search the media library

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response with the search result
    """
    query = request.GET.get("query")
    logger.debug("Media library searched with query %r", query)
    region = request.region

    media_files = MediaFile.search(region, query)
    directories = Directory.search(region, query)
    result = [d.serialize() for d in list(directories) + list(media_files)]

    logger.debug("Media library search results: %r", result)
    return JsonResponse({"data": result})


@json_response
@permission_required("cms.view_mediafile")
# pylint: disable=unused-argument
def get_file_usages_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View to search unused media files

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response with the search result
    """

    file = get_object_or_404(
        MediaFile.objects.filter(
            Q(region=request.region) | Q(region__isnull=True, is_hidden=False),
        ),
        id=request.GET.get("file"),
    )

    return JsonResponse({"data": file.serialize_usages()})


@json_response
@permission_required("cms.view_directory")
@permission_required("cms.view_mediafile")
# pylint: disable=unused-argument
def get_unused_media_files_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View to search unused media files

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response with the search result
    """

    unused_media_files = MediaFile.objects.filter(
        Q(region=request.region) | Q(region__isnull=True, is_hidden=False)
    ).filter_unused()

    result = [d.serialize() for d in unused_media_files]

    return JsonResponse({"data": result})


@require_POST
@permission_required("cms.upload_mediafile")
@json_response
# pylint: disable=unused-argument
def upload_file_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View to create a file via an AJAX upload.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
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
def edit_file_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View provides the edit of a file via AJAX.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
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
def replace_file_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View provides the replacement of a file via AJAX.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
    """
    region = request.region

    media_file = get_object_or_404(
        MediaFile.objects.filter(region=region), id=request.POST.get("id")
    )

    media_file_form = ReplaceMediaFileForm(
        user=request.user, data=request.POST, instance=media_file, files=request.FILES
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
def delete_file_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View to delete a file via an AJAX call.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
    """
    region = request.region

    media_file = get_object_or_404(
        MediaFile.objects.filter(region=region), id=request.POST.get("id")
    )

    # Check if the media file is in use
    if not media_file.is_deletable:
        return JsonResponse(
            {
                "messages": [
                    {
                        "type": "warning",
                        "text": _(
                            'File "{}" cannot be deleted because it is used as an icon or content.'
                        ).format(media_file.name),
                    }
                ],
            },
            status=400,
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
def create_directory_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View provides the frontend with the option to create a directory via AJAX.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
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
def edit_directory_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View provides the frontend with the option to modify a directory via AJAX.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
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
def delete_directory_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    View provides the frontend with the option to delete a directory via AJAX.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
    """
    region = request.region

    directory = get_object_or_404(
        Directory.objects.filter(region=region), id=request.POST.get("id")
    )
    serialized = directory.serialize()

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
            "directory": serialized,
        }
    )


@require_POST
@permission_required("cms.change_directory")
@permission_required("cms.change_mediafile")
@json_response
# pylint: disable=unused-argument
def move_file_ajax(
    request: HttpRequest, region_slug: str | None = None
) -> JsonResponse:
    """
    This view provides the frontend with the option to move files via AJAX.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: JSON response which indicates error or success
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
