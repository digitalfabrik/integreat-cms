from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from ...decorators import region_permission_required, staff_required
from ...models import Event


@login_required
@region_permission_required
def archive(request, event_id, region_slug, language_code):
    event = Event.objects.get(id=event_id)

    if not request.user.has_perm('cms.edit_events'):
        raise PermissionDenied

    event.archived = True
    event.save()

    messages.success(request, _('Event was successfully archived.'))

    return redirect('events', **{
        'region_slug': region_slug,
        'language_code': language_code,
    })


@login_required
@region_permission_required
def restore(request, event_id, region_slug, language_code):
    event = Event.objects.get(id=event_id)

    if not request.user.has_perm('cms.edit_events'):
        raise PermissionDenied

    event.archived = False
    event.save()

    messages.success(request, _('Event was successfully restored.'))

    return redirect('events', **{
        'region_slug': region_slug,
        'language_code': language_code,
    })


@login_required
@staff_required
def delete(request, event_id, region_slug, language_code):

    event = Event.objects.get(id=event_id)
    if event.recurrence_rule:
        event.recurrence_rule.delete()
    event.delete()
    messages.success(request, _('Event was successfully deleted.'))

    return redirect('events', **{
        'region_slug': region_slug,
        'language_code': language_code,
    })
