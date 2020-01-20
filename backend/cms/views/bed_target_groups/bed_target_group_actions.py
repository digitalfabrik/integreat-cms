#import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from ...decorators import staff_required
from ...models import BedTargetGroup

@login_required
@staff_required
def delete_bed_target_group(request, bed_target_group_id):

    bed_target_group = BedTargetGroup.objects.get(id=bed_target_group_id)
    bed_target_group.delete()
    messages.success(request, _('Bed Target Group was successfully deleted.'))

    return redirect('bed_target_groups')
    