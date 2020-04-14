from datetime import timedelta
from django.utils import timezone

import requests

from backend import settings
from cms.models import Configuration

from .crypto_tools import (
    derive_id_from_domain_and_public_key,
    derive_public_key_from_private_key,
    generate_private_key
)
from .models import CMSCache, RegionCache
from .request_sender import (
    request_cms_data,
    request_cms_domains, request_cms_region_list
)

def activate_federation_feature():
    Configuration.objects.get_or_create(key="federation_private_key", defaults={"value": generate_private_key()})


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
        name, public_key = request_cms_data(domain)
        cms_id = derive_id_from_domain_and_public_key(domain, public_key)
        CMSCache.objects.update_or_create(id=cms_id, defaults={
            "name": name,
            "domain": domain,
            "public_key": public_key,
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

def get_id() -> str:
    return derive_id_from_domain_and_public_key(get_domain(), get_public_key())


def get_name() -> str:
    return settings.FEDERATION["name"]


def get_domain() -> str:
    return settings.FEDERATION["domain"]


def get_public_key() -> str:
    return derive_public_key_from_private_key(get_private_key())


def get_private_key() -> str:
    return Configuration.objects.get(key="federation_private_key").value
