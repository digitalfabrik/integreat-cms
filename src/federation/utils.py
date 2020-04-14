from datetime import timedelta
from django.utils import timezone

import requests

from backend import settings

from .models import CMSCache, RegionCache
from .request_sender import (
    request_cms_domains, request_cms_region_list, request_cms_name
)


def update_cms_data():
    """
    Asks all known CMSs for new cms_ids and asks for data of the new CMSs
    """
    known_domains = {cms.domain for cms in CMSCache.objects.all()}
    new_domains = set()
    for domain in known_domains:
        handle_domain(domain)
        new_domains = new_domains.union([x for x in request_cms_domains(domain) if x not in known_domains])
    for domain in new_domains:
        handle_domain(domain)
    clean_cms_cache()
    for cms_cache in CMSCache.objects.all():
        update_cms_region_list(cms_cache)

def handle_domain(domain: str):
    try:
        name = request_cms_name(domain)
        CMSCache.objects.update_or_create(domain=domain, defaults={
            "name": name,
            "last_contact": timezone.now()
        })
    except requests.RequestException:
        pass

def clean_cms_cache():
    for cms in CMSCache.objects.filter(last_contact__lte=timezone.now() - timedelta(3)):
        cms.delete()

def update_cms_region_list(cms_cache: CMSCache):
    region_list = request_cms_region_list(cms_cache.domain)
    for region in region_list:
        RegionCache.objects.update_or_create(parentCMS=cms_cache, path=region["path"], defaults={
            "postal_code": region["plz"],
            "prefix": region["prefix"],
            "name_without_prefix": region["name_without_prefix"],
            "aliases": region["aliases"],
            "latitude": region["latitude"],
            "longitude": region["longitude"],
        })
    #todo: lösche alle anderen regionen (achtung: bei RequestException wird leeres Array returnt)

def get_name() -> str:
    return settings.FEDERATION["name"]


def get_domain() -> str:
    return settings.FEDERATION["domain"]
