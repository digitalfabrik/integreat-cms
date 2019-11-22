from django.http import HttpResponse

from .request_sender import (
    send_offer,
    ask_for_cms_data,
)
from .utils import (
    get_domain,
    get_id,
    get_name,
    get_private_key,
    get_public_key,
    update_cms_data,
)


def test(request):
    print(get_id())
    print(get_name())
    print(get_domain())
    print(get_public_key())
    print(get_private_key())
    return HttpResponse("test")


def test_send_offer(request):
    domain = "localhost:8000"
    send_offer(domain)
    return HttpResponse("Angebot gesendet.")


def test_update(request):
    update_cms_data()
    return HttpResponse("Alles upgedatet.")


def test_ask(request):
    domain = "localhost:8000"
    cms_id = "bdd9bfbd9742d81a1680"
    ask_for_cms_data(domain, cms_id)
    return HttpResponse("Anfrage gestellt.")
