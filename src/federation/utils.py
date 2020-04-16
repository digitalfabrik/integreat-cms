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
    cms_list = CMSCache.objects.all()
    known_domains = {cms.domain for cms in cms_list}
    new_domains = set()
    for cms in cms_list:
        handle_cms(cms)
        new_domains = new_domains.union([x for x in request_cms_domains(cms) if x not in known_domains])
    for domain in new_domains:
        handle_unknown_domain(domain)
    clean_cms_cache()

def handle_cms(cms: CMSCache):
    try:
        name = request_cms_name(cms.domain)
        cms.name = name
        if cms.active:
            update_cms_region_list(cms)
        cms.persist_successful_contact_attempt()
    except requests.RequestException:
        cms.persist_failed_contact_attempt()

def handle_unknown_domain(domain: str):
    try:
        name = request_cms_name(domain)
        cms = CMSCache(name=name, domain=domain)
        cms.save()
    except requests.RequestException:
        pass

def clean_cms_cache():
    for cms in CMSCache.objects.filter(last_contact__lte=timezone.now() - timedelta(3)):
        cms.delete()

def update_cms_region_list(cms_cache: CMSCache):
    region_list = request_cms_region_list(cms_cache)
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
