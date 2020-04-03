from django.http import JsonResponse, HttpResponse

from cms.models import Region
from .pages import transform_page

def single_page(request, region_slug, language_code):
    if request.GET.get('id', ''):
        region = Region.objects.get(slug=region_slug)
        page_translation = None
        page = region.pages.filter(id=int(request.GET.get('id', '')))
        if page:
            page_translation = page.first().get_public_translation(language_code)
            return JsonResponse(transform_page(page_translation), safe=False)
    elif request.GET.get('url', ''):
        region = Region.objects.get(slug=region_slug)
        for page in region.pages.all():
            page_translations = page.translations.all()
            for translation in page_translations:
                if (translation.permalink == request.GET.get('url', '')) & (translation != None) :
                    return JsonResponse(transform_page(translation), safe=False)
    
    return HttpResponse('The requested Page does not exist', status=404)
    