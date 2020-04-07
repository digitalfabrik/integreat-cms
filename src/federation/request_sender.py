import json
import requests


def request_cms_domains(domain: str) -> [str]:
    """
    Asks the cms (specified by domain) for ids
    Returns: the list of ids
    """
    response = send_federation_request(domain, "domains")
    response_list = json.loads(response)
    return response_list

def request_cms_data(domain: str) -> (str, str):
    response = send_federation_request(domain, "cms-data")
    response_dict = json.loads(response)
    return response_dict["name"], response_dict["public_key"]


def send_offer(domain: str):
    from federation.utils import get_domain
    send_federation_request(domain, "offer", {"domain": get_domain()})


def send_federation_request(domain: str, tail: str, params=None) -> str:
    return requests.get("http://" + domain + "/federation/" + tail, params).text
