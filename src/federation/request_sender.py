import json
import requests
from requests import Response


def request_cms_domains(domain: str) -> [str]:
    """
    Asks the cms (specified by domain) for ids
    Returns: the list of ids
    """
    try:
        response = send_federation_request(domain, "cms-domains")
        response_list = json.loads(response)
        return response_list
    except requests.RequestException:
        return []

def request_cms_name(domain: str) -> str:
    return send_federation_request(domain, "cms-name")

def send_offer(domain: str):
    try:
        from federation.utils import get_domain
        send_federation_request(domain, "offer", {"domain": get_domain()})
    except requests.RequestException:
        pass

def request_cms_region_list(domain: str):
    a = requests.get("http://" + domain + "/api/regions/live").text
    return json.loads(a)

def send_federation_request(domain: str, tail: str, params=None) -> str:
    return requests.get("http://" + domain + "/federation/" + tail, params).text
