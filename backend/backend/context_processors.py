from cms.models.site import Site

def site_slug_processor(request):
    site = Site.get_current_site(request)
    if site:
        sites = Site.objects.exclude(slug=site.slug)
    else:
        sites = Site.objects.all()
    return {'sites': sites, 'site': site}
