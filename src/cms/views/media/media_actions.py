"""
This module contains view actions for media related objects.
"""
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from api.decorators import json_response
from ...decorators import region_permission_required
from ...models import Document, Region, Directory
from ...utils.media_utils import attach_file
from ...constants import allowed_media


@require_POST
@login_required
@region_permission_required
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
    region = Region.get_current_region(request)

    directory_id = request.POST.get("parentDirectory", 0)
    directory = None

    if int(directory_id) != 0:
        directory = get_object_or_404(
            Directory.objects.filter(region=region), id=directory_id
        )

    if "upload" in request.FILES:
        file_type = request.FILES["upload"].content_type
        if file_type in dict(allowed_media.CHOICES):
            document = Document()
            document.region = region
            document.parent_directory = directory
            document.name = request.FILES["upload"].name
            attach_file(document, request.FILES["upload"])
            document.save()
            return JsonResponse({"success": True})
        return JsonResponse(
            {
                "success": False,
                "error": _(
                    "Unsupported File can't be uploaded. Only Images and PDF allowed."
                ),
            },
            status=403,
        )

    return JsonResponse(
        {"success": False, "error": _("No file was uploaded")}, status=400
    )


@require_POST
@login_required
@region_permission_required
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
    region = Region.get_current_region(request)

    json_data = json.loads(request.body.decode("utf-8"))
    media_element = get_object_or_404(
        Document.objects.filter(region=region), id=json_data["id"]
    )

    media_element.delete()

    return JsonResponse({"success": True})


@login_required
@region_permission_required
@json_response
# pylint: disable=unused-argument
def get_directory_path_ajax(request, region_slug=None):
    """
    View provides the frontend with the current directory path for the breadcrumps.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = Region.get_current_region(request)

    directory_id = request.GET.get("directory", 0)
    directory_path = []

    if int(directory_id) != 0:
        directory = get_object_or_404(
            Directory.objects.filter(Q(region=region) | Q(region__isnull=True)),
            id=directory_id,
        )

        while directory:
            directory_path.insert(0, directory.serialize())
            directory = directory.parent

    return JsonResponse({"success": True, "data": directory_path})


@login_required
@region_permission_required
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
    region = Region.get_current_region(request)

    directory_id = request.GET.get("directory", 0)
    directory = None

    if int(directory_id) != 0:
        directory = get_object_or_404(
            Directory.objects.filter(Q(region=region) | Q(region__isnull=True)),
            id=directory_id,
        )

    documents = Document.objects.filter(
        Q(region=region) | Q(region__isnull=True), Q(parent_directory=directory)
    )
    directories = Directory.objects.filter(
        Q(region=region) | Q(region__isnull=True), parent=directory
    )

    result = list(map(lambda d: d.serialize(), list(directories) + list(documents)))

    return JsonResponse({"success": True, "data": result})


@require_POST
@login_required
@region_permission_required
@json_response
# pylint: disable=unused-argument
def edit_media_element_ajax(request, region_slug=None):
    """
    View provides the edit of a file via AJAX.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = Region.get_current_region(request)

    json_data = json.loads(request.body.decode("utf-8"))
    media_element_id = json_data["id"]
    media_element = get_object_or_404(
        Document.objects.filter(region=region), id=media_element_id
    )

    media_element.name = json_data["name"]
    media_element.alt_text = json_data["alt_text"]
    media_element.save()

    return JsonResponse({"success": True})


@require_POST
@login_required
@region_permission_required
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
    region = Region.get_current_region(request)

    json_data = json.loads(request.body.decode("utf-8"))
    parent_directory = None
    if int(json_data["parentDirectory"]) != 0:
        parent_directory = get_object_or_404(
            Directory.objects.filter(region=region), id=json_data["parentDirectory"]
        )

    queryset = Directory.objects
    if region:
        # If directory is created for a region, only limit choices to the global library and the regional one
        queryset = queryset.filter(Q(region=region) | Q(region__isnull=True))
    if queryset.filter(
        parent=parent_directory,
        name=json_data["directoryName"],
    ).exists():
        return JsonResponse({"error": _("Directory already exists")}, status=400)

    Directory.objects.create(
        name=json_data["directoryName"], parent=parent_directory, region=region
    )

    return JsonResponse({"success": True})


@require_POST
@login_required
@region_permission_required
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
    region = Region.get_current_region(request)

    json_data = json.loads(request.body.decode("utf-8"))

    directory = get_object_or_404(
        Directory.objects.filter(region=region), id=json_data["id"]
    )

    directory.delete()

    return JsonResponse({"success": True})


@require_POST
@login_required
@region_permission_required
@json_response
# pylint: disable=unused-argument
def update_directory_ajax(request, region_slug=None):
    """
    View provides the frontend with the option to delete a directory via AJAX.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: JSON response which indicates error or success
    :rtype: ~django.http.JsonResponse
    """
    region = Region.get_current_region(request)

    json_data = json.loads(request.body.decode("utf-8"))
    directory_id = json_data["id"]
    directory_element = get_object_or_404(
        Directory.objects.filter(region=region), id=directory_id
    )

    directory_element.name = json_data["name"]
    directory_element.save()

    return JsonResponse({"success": True})
