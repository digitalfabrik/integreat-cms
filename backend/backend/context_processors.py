from cms.models.region import Region

def region_slug_processor(request):
    region = Region.get_current_region(request)
    if region:
        regions = Region.objects.exclude(slug=region.slug)
    else:
        regions = Region.objects.all()
    return {'regions': regions, 'region': region}
