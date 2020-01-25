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

from ...constants import status
from ...decorators import region_permission_required
from ...forms.accommodations import AccommodationForm, AccommodationTranslationForm
from ...models import Accommodation, AccommodationTranslation, Region, Language, Beds

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class AccommodationView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_accommodations'
    raise_exception = True

    template_name = 'accommodations/accommodation_form.html'
    base_context = {'current_menu_item': 'accommodations'}

    def get(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get('region_slug'))

        language = Language.objects.get(code=kwargs.get('language_code'))

        # get accommodation and translation objects if they exist
        accommodation = Accommodation.objects.filter(id=kwargs.get('accommodation_id')).first()
        accommodation_translation = AccommodationTranslation.objects.filter(
            accommodation=accommodation,
            language=language,
        ).first()

        # Make form disabled if user has no permission to edit the page
        if not request.user.has_perm('cms.edit_accommodations'):
            disabled = True
            messages.warning(request, _("You don't have the permission to edit this Accommodation."))
        elif accommodation and accommodation.archived:
            disabled = True
            messages.warning(request, _("You cannot edit this Accommodation because it is archived."))
        else:
            disabled = False

        accommodation_form = AccommodationForm(
            instance=accommodation,
            disabled=disabled,
        )
        accommodation_translation_form = AccommodationTranslationForm(
            instance=accommodation_translation,
            disabled=disabled,
        )

        return render(request, self.template_name, {
            **self.base_context,
            'accommodation_form': accommodation_form,
            'accommodation_translation_form': accommodation_translation_form,
            'language': language,
            # Languages for tab view
            'languages': region.languages if accommodation else [language],
        })

    # pylint: disable=too-many-branches,too-many-locals,unused-argument
    def post(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get('region_slug'))
        language = Language.objects.get(code=kwargs.get('language_code'))

        accommodation_instance = Accommodation.objects.filter(id=kwargs.get('accommodation_id')).first()

        accommodation_translation_instance = AccommodationTranslation.objects.filter(
            accommodation=accommodation_instance,
            language=language,
        ).first()

        accommodation_form = AccommodationForm(
            request.POST,
            instance=accommodation_instance,
        )
        accommodation_translation_form = AccommodationTranslationForm(
            request.POST,
            instance=accommodation_translation_instance,
            region=region,
            language=language,
        )

        if (
                not accommodation_form.is_valid() or
                not accommodation_translation_form.is_valid()
        ):

            # Add error messages
            for form in [accommodation_form, accommodation_translation_form]:
                for field in form:
                    for error in field.errors:
                        messages.error(request, _(field.label) + ': ' + _(error))
                for error in form.non_field_errors():
                    messages.error(request, _(error))

        elif (
                not accommodation_form.has_changed() and
                not accommodation_translation_form.has_changed()
        ):

            messages.info(request, _('No changes detected.'))

        else:

            if accommodation_translation_form.instance.status == status.PUBLIC:
                if not request.user.has_perm('cms.publish_accommodations'):
                    raise PermissionDenied

            accommodation = accommodation_form.save(
                region=region,
            )
            accommodation_translation = accommodation_translation_form.save(
                accommodation=accommodation,
                user=request.user,
            )
            published = accommodation_translation.status == status.PUBLIC
            if accommodation_form.data.get('submit_archive'):
                # archive button has been submitted
                messages.success(request, _('Accommodation was successfully archived.'))
            elif not accommodation_instance:
                if published:
                    messages.success(request, _('Accommodation was successfully created and published.'))
                else:
                    messages.success(request, _('Accommodation was successfully created.'))
                return redirect('edit_accommodation', **{
                    'accommodation_id': accommodation.id,
                    'region_slug': region.slug,
                    'language_code': language.code,
                })
            elif not accommodation_translation_instance:
                if published:
                    messages.success(request, _('Accommodation Translation was successfully created and published.'))
                else:
                    messages.success(request, _('Accommodation Translation was successfully created.'))
            else:
                if published:
                    messages.success(request, _('Accommodation Translation was successfully published.'))
                else:
                    messages.success(request, _('Accommodation Translation was successfully saved.'))

        return render(request, self.template_name, {
            **self.base_context,
            'accommodation_form': accommodation_form,
            'accommodation_translation_form': accommodation_translation_form,
            'language': language,
            # Languages for tab view
            'languages': region.languages if accommodation_instance else [language],
        })
