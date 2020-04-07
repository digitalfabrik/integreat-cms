from django.http import (
    JsonResponse,
    HttpResponse,
    HttpRequest,
)

from .models import CMSCache
from .utils import (
    get_public_key,
    handle_domain, get_name)


def cms_domains(request: HttpRequest):
    """
    :param request:
    :return: a JSON-response containing ids of all known cms (not the own id)
    """
    response_list = [cms.domain for cms in CMSCache.objects.all()]
    return JsonResponse(response_list, safe=False)

def cms_data(request: HttpRequest):
    """
    :return: a JSON-response containing the own name and public key
    """
    response_dict = {
        "name": get_name(),
        "public_key": get_public_key()
    }
    return JsonResponse(response_dict, safe=False)


def receive_offer(request: HttpRequest):
    domain: str = request.GET["domain"]
    handle_domain(domain)
    return HttpResponse()
