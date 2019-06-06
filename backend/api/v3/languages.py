from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse

from cms.models import Site


def languages(_, site_slug):
    try:
        site = Site.objects.get(slug=site_slug)

        result = list(map(lambda l: {
            'id': l.language.id,
            'code': l.language.code,
            'native_name': l.language.name,
            'dir': l.language.text_direction,
        }, site.language_tree_nodes.filter(active=True)))
        return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays
    except ObjectDoesNotExist:
        return HttpResponse(f'No Site found with name "{site_slug}".', content_type='text/plain',
                            status=404)
