from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from api.decorators import feedback_handler
from cms.models import Region, EventListFeedback


@feedback_handler
# pylint: disable=unused-argument
def event_list_feedback(data, region_slug, language_code, comment, emotion, is_technical):
    try:
        region = Region.objects.get(slug=region_slug)
        EventListFeedback.objects.create(region=region, emotion=emotion, comment=comment, is_technical=is_technical)
        return JsonResponse({'success': 'Feedback successfully submitted'}, status=201)
    except ObjectDoesNotExist:
        return JsonResponse({'error': f'No region found with slug "{region_slug}"'}, status=404)
