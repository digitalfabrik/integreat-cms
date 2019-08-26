from django.http import (
    JsonResponse,
    HttpResponse,
    HttpRequest,
)

from .models import CMSCache
from .request_sender import ask_for_cms_data
from .utils import (
    add_or_override_cms_cache,
    get_id,
    get_name,
    get_public_key,
)


def cms_ids(request: HttpRequest):
    """
    :param request:
    :return: a JSON-response containing ids of all known cms (not the own id)
    """
    response_list = [
        cmsCacheEntry.id for cmsCacheEntry in CMSCache.objects.filter(share_with_others=True)
    ] + [get_id()]
    return JsonResponse(response_list, safe=False)


def cms_domain(request, cms_id):
    """
    Returns: If cms_id is present in the model CMSCache: the domain of this cms, null if not
    """
    cms = CMSCache.objects.get(id=cms_id)
    return HttpResponse(cms.domain)
    #todo: error handling: cms_id not present


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
    cms_id = ''
    (name, public_key) = ask_for_cms_data(domain, cms_id)
    add_or_override_cms_cache(name, domain, public_key)
    return HttpResponse()
