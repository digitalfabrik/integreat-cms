from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse

from cms.models import Site


def languages(_, site_name):
    try:
        site = Site.objects.get(name=site_name)

        result = list(map(lambda l: {
            'code': l.code,
            'native_name': l.title,
            'dir': l.text_direction,
        }, site.supported_languages.all()))
        return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays
    except ObjectDoesNotExist:
        return HttpResponse(f'No Site found with name "{site_name}".', content_type='text/plain',
                            status=404)
