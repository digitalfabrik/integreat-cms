"""
A view representing an instance of a accommodationnt of interest. Accommodations can be added, changed or retrieved via this view.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.forms.models import inlineformset_factory
from django.db.models import Sum

from ...models import Accommodation, Beds

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class BedsView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_beds'
    raise_exception = True

    template_name = 'accommodations/bed_management.html'
    base_context = {'current_menu_item': 'accommodations'}


    def get(self, request, *args, **kwargs):
        accommodation = Accommodation.objects.get(id=kwargs.get('accommodation_id'))
        accommodation_translation = accommodation.get_translation(kwargs.get('language_code'))

        beds_formset_factory = inlineformset_factory(
            Accommodation,
            Beds,
            fields=('num_beds_allocated',),
            extra=0,
        )
        beds_formset = beds_formset_factory(instance=accommodation)

        return render(request, self.template_name, {
            **self.base_context,
            'accommodation_title': accommodation_translation.title,
            'beds_formset' : beds_formset,
            'beds_sum': accommodation.beds.aggregate(Sum('num_beds'))['num_beds__sum'],
            'beds_allocated_sum': accommodation.beds.aggregate(Sum('num_beds_allocated'))['num_beds_allocated__sum'],
        })

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        accommodation = Accommodation.objects.get(id=kwargs.get('accommodation_id'))
        accommodation_translation = accommodation.get_translation(kwargs.get('language_code'))

        beds_formset_factory = inlineformset_factory(
            Accommodation,
            Beds,
            fields=('num_beds_allocated',),
            extra=0,
        )
        beds_formset = beds_formset_factory(request.POST, instance=accommodation)

        if not beds_formset.is_valid():
            # Add error messages
            for form in beds_formset:
                for field in form:
                    for error in field.errors:
                        messages.error(request, _(error))
                for error in form.non_field_errors():
                    messages.error(request, _(error))
        elif not beds_formset.has_changed():
            messages.info(request, _('No changes detected.'))
        else:
            beds_formset.save()
            # Re-initialize form set to make sure deleted rows disappear
            beds_formset = beds_formset_factory(instance=accommodation)
            messages.success(request, _('Beds allocation was successfully saved.'))

        return render(request, self.template_name, {
            **self.base_context,
            'accommodation_title': accommodation_translation.title,
            'beds_formset': beds_formset,
            'beds_sum': accommodation.beds.aggregate(Sum('num_beds'))['num_beds__sum'],
            'beds_allocated_sum': accommodation.beds.aggregate(Sum('num_beds_allocated'))['num_beds_allocated__sum'],
        })
