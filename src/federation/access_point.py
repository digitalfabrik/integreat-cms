from django.http import (
    JsonResponse,
    HttpResponse,
    HttpRequest,
)

from .models import CMSCache
from .utils import (
    handle_unknown_domain, get_name, handle_cms)


def cms_domains(request: HttpRequest):
    """
    :param request:
    :return: a JSON-response containing ids of all known cms (not the own id)
    """
    response_list = [cms.domain for cms in CMSCache.objects.all()]
    return JsonResponse(response_list, safe=False)

def cms_name(request: HttpRequest):
    """
    :return: a JSON-response containing the own name and public key
    """
    return HttpResponse(get_name())


def receive_offer(request: HttpRequest):
    domain: str = request.GET["domain"]
    a = CMSCache.objects.filter(domain=domain)
    if a.exists():
        handle_cms(a.first())
    else:
        handle_unknown_domain(domain)
    return HttpResponse()
