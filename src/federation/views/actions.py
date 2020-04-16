from django.shortcuts import redirect

from federation.models import CMSCache
from federation.utils import handle_cms


def activate(request, cms_id: str):
    cms = CMSCache.objects.get(id=cms_id)
    cms.active = True
    cms.save()
    handle_cms(cms)
    return redirect('federation')

def deactivate(request, cms_id: str):
    cms = CMSCache.objects.get(id=cms_id)
    cms.active = False
    cms.save()
    return redirect('federation')

def check_availability(request, cms_id: str):
    cms = CMSCache.objects.get(id=cms_id)
    handle_cms(cms)
    return redirect('federation')
