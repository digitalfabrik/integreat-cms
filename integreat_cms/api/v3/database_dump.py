from django.core.exceptions import PermissionDenied
from django.http import FileResponse, HttpRequest

from integreat_cms.database_dump.dump import dump_database


def database_dump(request: HttpRequest) -> FileResponse:
    """
    Creates a database dump and serializes it as json.

    :param request: The request
    :return: A FileResponse with the serialized data
    """
    if not request.user.is_superuser:
        raise PermissionDenied(
            f"{request.user} does not have permission to generate a database dump (You might need to log in first)"
        )

    return FileResponse(dump_database(), content_type="application/json")
