"""
A view representing an instance of a point of interest. POIs can be added, changed or retrieved via this view.
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
from ...forms.pois import POIForm, POITranslationForm
from ...models import POI, POITranslation, Region, Language

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class POIView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_pois'
    raise_exception = True

    template_name = 'pois/poi_form.html'
    base_context = {'current_menu_item': 'pois'}

    def get(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get('region_slug'))

        language = Language.objects.get(code=kwargs.get('language_code'))

        # get poi and translation objects if they exist
        poi = POI.objects.filter(id=kwargs.get('poi_id')).first()
        poi_translation = POITranslation.objects.filter(
            poi=poi,
            language=language,
        ).first()

        # Make form disabled if user has no permission to edit the page
        if not request.user.has_perm('cms.edit_pois'):
            disabled = True
            messages.warning(request, _("You don't have the permission to edit this POI."))
        elif poi and poi.archived:
            disabled = True
            messages.warning(request, _("You cannot edit this POI because it is archived."))
        else:
            disabled = False

        poi_form = POIForm(
            instance=poi,
            disabled=disabled,
        )
        poi_translation_form = POITranslationForm(
            instance=poi_translation,
            disabled=disabled,
        )

        return render(request, self.template_name, {
            **self.base_context,
            'poi_form': poi_form,
            'poi_translation_form': poi_translation_form,
            'language': language,
            # Languages for tab view
            'languages': region.languages if poi else [language],
        })

    # pylint: disable=too-many-branches,too-many-locals,unused-argument
    def post(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get('region_slug'))
        language = Language.objects.get(code=kwargs.get('language_code'))

        poi_instance = POI.objects.filter(id=kwargs.get('poi_id')).first()
        poi_translation_instance = POITranslation.objects.filter(
            poi=poi_instance,
            language=language,
        ).first()

        poi_form = POIForm(
            request.POST,
            instance=poi_instance,
        )
        poi_translation_form = POITranslationForm(
            request.POST,
            instance=poi_translation_instance,
            region=region,
            language=language,
        )

        if (
                not poi_form.is_valid() or
                not poi_translation_form.is_valid()
        ):

            # Add error messages
            for form in [poi_form, poi_translation_form]:
                for field in form:
                    for error in field.errors:
                        messages.error(request, _(field.label) + ': ' + _(error))
                for error in form.non_field_errors():
                    messages.error(request, _(error))

        elif (
                not poi_form.has_changed() and
                not poi_translation_form.has_changed()
        ):

            messages.info(request, _('No changes detected.'))

        else:

            if poi_translation_form.instance.status == status.PUBLIC:
                if not request.user.has_perm('cms.publish_pois'):
                    raise PermissionDenied

            poi = poi_form.save(
                region=region,
            )
            poi_translation = poi_translation_form.save(
                poi=poi,
                user=request.user,
            )
            published = poi_translation.public and 'public' in poi_translation_form.changed_data
            if poi_form.data.get('submit_archive'):
                # archive button has been submitted
                messages.success(request, _('POI was successfully archived.'))
            elif not poi_instance:
                if published:
                    messages.success(request, _('POI was successfully created and published.'))
                else:
                    messages.success(request, _('POI was successfully created.'))
                    return redirect('edit_poi', **{
                        'poi_id': poi.id,
                        'region_slug': region.slug,
                        'language_code': language.code,
                    })
            elif not poi_translation_instance:
                if published:
                    messages.success(request, _('POI Translation was successfully created and published.'))
                else:
                    messages.success(request, _('POI Translation was successfully created.'))
            else:
                if published:
                    messages.success(request, _('POI Translation was successfully published.'))
                else:
                    messages.success(request, _('POI Translation was successfully saved.'))

        return render(request, self.template_name, {
            **self.base_context,
            'poi_form': poi_form,
            'poi_translation_form': poi_translation_form,
            'language': language,
            # Languages for tab view
            'languages': region.languages if poi_instance else [language],
        })
