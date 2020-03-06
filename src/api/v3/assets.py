import os
from django.http.response import Http404, HttpResponse
from cms.models import Document
from backend.settings import MEDIA_ROOT


def single_asset(request, asset_id, asset_name):
    document = Document.objects.get(id=asset_id, name=asset_name)
    if not document:
        raise Http404
    file_path = os.path.join(MEDIA_ROOT, document.file.path)
    if os.path.exists(file_path):
        with open(file_path, "rb") as fh:
            response = HttpResponse(fh.read(), content_type=document.file.type)
            response["Content-Disposition"] = "inline; filename=" + document.name
            return response
    raise Http404
