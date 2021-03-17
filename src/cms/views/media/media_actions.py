"""
This module contains view actions for media related objects.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from ...decorators import region_permission_required
from ...models import Document, Region


@require_POST
@login_required
@region_permission_required
# pylint: disable=unused-argument
def delete_file(request, document_id, region_slug):
    """
    This view deletes a file both from the database and the file system.

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param document_id: The id of the document which is being deleted
    :type document_id: int

    :param region_slug: The slug of the region to which this document belongs
    :type region_slug: str

    :return: A redirection to the media library
    :rtype: ~django.http.HttpResponseRedirect
    """
    region = Region.get_current_region(request)

    if request.method == "POST":
        document = Document.objects.get(id=document_id)
        document.delete()

    return redirect("media", **{"region_slug": region.slug})
