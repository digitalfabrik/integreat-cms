import requests

from federation.models import CMSCache


def request_cms_domains(cms: CMSCache) -> [str]:
    """
    Asks the cms (specified by domain) for ids
    Returns: the list of ids
    """
    try:
        r = requests.get("http://" + cms.domain + "/federation/cms-domains")
        if r.ok:
            res = r.json()
            cms.persist_successful_contact_attempt()
            return res
    except (requests.RequestException, ValueError):
        pass
    cms.persist_failed_contact_attempt()
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

def request_cms_region_list(cms: CMSCache):
    try:
        r = requests.get("http://" + cms.domain + "/api/regions/live")
        if r.ok:
            return r.json()
    except ValueError:
        pass
    raise requests.RequestException
