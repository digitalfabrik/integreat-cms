"""
A view representing an instance of a accommodationnt of interest. Accommodations can be added, changed or retrieved via this view.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.forms.formsets import formset_factory
from django.forms import modelformset_factory
from django.forms.models import inlineformset_factory
from django.db.models import Sum

from ...forms.accommodations import BedsGeneralCreationForm

from ...models import Accommodation, Beds, BedTargetGroup

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class BedsView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_accommodations'
    raise_exception = True

    template_name = 'accommodations/beds_general_creation_form.html'
    base_context = {'current_menu_item': 'beds'}

    def get(self, request, *args, **kwargs):
        BedsFormSet = inlineformset_factory(Accommodation, Beds, fields=('num_beds', 'num_free_beds'), extra=1)
        accommodation = Accommodation.objects.filter(id=kwargs.get('accommodation_id')).first()

        beds = accommodation.beds.all()
        beds_sum = beds.aggregate(Sum('num_beds'))
        if not request.user.has_perm('cms.edit_accommodations'):
            disabled = True
            messages.warning(request, _("You don't have the permission to edit Beds."))
        else:
            disabled = False

        formset = BedsFormSet(request.GET or None, instance=accommodation)
        return render(request, self.template_name, {
            **self.base_context,
            'formset' : formset,
            'beds': beds,
            'beds_sum': beds_sum['num_beds__sum']
        })

    def post(self, request, *args, **kwargs):
        accommodation = Accommodation.objects.filter(id=kwargs.get('accommodation_id')).first()
        BedsFormSet = inlineformset_factory(Accommodation, Beds, fields=('num_beds', 'num_free_beds'))

        formset = BedsFormSet(request.POST, instance=accommodation)

        if formset.is_valid():
            formset.save()
                
            return render(request, self.template_name, {
                'formset': formset
            })
