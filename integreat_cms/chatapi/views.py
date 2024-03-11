"""
This module includes functions related to the regions API endpoint.
"""
from django.http import Http404, JsonResponse
from .models import ChatSession
from ..decorators import json_response


@json_response
# pylint: disable=unused-argument
def region_by_slug(request: HttpRequest, region_slug: str) -> JsonResponse:
    """
    Retrieve a single region and transform result into JSON

    :return: JSON object according to APIv3 live regions endpoint definition
    """
    session_token = request.GET["session_id"]
    chat_session = ChatSession.object.filter(session_token=session_token)
    if not chat_session:
        ZammadHandler.create_ticket()
    if request.method == "GET":
        response = get_last_message_from_zammad()
    elif request.method == "POST":
        response = post_message_to_zammad()

    return JsonResponse(response)
