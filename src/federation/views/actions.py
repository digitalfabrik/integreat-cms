from django.shortcuts import redirect

from federation.models import CMSCache

def verify(request, cms_id:str):
    cms = CMSCache.objects.get(id=cms_id)
    cms.verified = True
    cms.save()
    return redirect('federation')

def revoke_verification(request, cms_id:str):
    cms = CMSCache.objects.get(id=cms_id)
    cms.verified = False
    cms.save()
    return redirect('federation')
