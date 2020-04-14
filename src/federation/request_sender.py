import requests


def request_cms_domains(domain: str) -> [str]:
    """
    Asks the cms (specified by domain) for ids
    Returns: the list of ids
    """
    try:
        r = requests.get("http://" + domain + "/federation/cms-domains")
        if r.ok:
            return r.json()
    except (requests.RequestException, ValueError):
        return []

def request_cms_name(domain: str) -> str:
    r = requests.get("http://" + domain + "/federation/cms-name")
    if r.ok:
        return r.text
    else:
        raise requests.RequestException

def send_offer(domain: str):
    try:
        from federation.utils import get_domain
        requests.get("http://" + domain + "/federation/offer", {"domain": get_domain()})
    except requests.RequestException:
        pass

def request_cms_region_list(domain: str):
    try:
        r = requests.get("http://" + domain + "/api/regions/live")
        if r.ok:
            return r.json()
        else:
            return []
    except (requests.RequestException, ValueError):
        return []
