"""
A view representing an instance of a point of interest. POIs can be added, changed or retrieved via this view.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from .poi_form import POIForm, POITranslationForm
from ...models import POI, POITranslation, Region, Language
from ...decorators import region_permission_required


logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class POIView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_pois'
    raise_exception = True

    template_name = 'pois/poi.html'
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

        poi_form = POIForm(
            instance=poi,
            region=region,
        )
        poi_translation_form = POITranslationForm(
            instance=poi_translation,
        )

        return render(request, self.template_name, {
            **self.base_context,
            'poi_form': poi_form,
            'poi_translation_form': poi_translation_form,
            'poi': poi,
            'language': language,
            'languages': region.languages,
        })

    # pylint: disable=R0912
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
            region=region,
        )
        poi_translation_form = POITranslationForm(
            request.POST,
            instance=poi_translation_instance,
            region=region,
            language=language,
        )

        # TODO: error handling
        if poi_form.is_valid() and poi_translation_form.is_valid():
            if poi_form.has_changed() or poi_translation_form.has_changed():
                poi = poi_form.save()
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
            else:
                messages.info(request, _('No changes detected.'))

            return redirect('edit_poi', **{
                'poi_id': poi.id,
                'region_slug': region.slug,
                'language_code': language.code,
            })

        messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            **self.base_context,
            'poi_form': poi_form,
            'poi_translation_form': poi_translation_form,
            'poi': poi_instance,
            'language': language,
            'languages': region.languages,
        })


@login_required
@region_permission_required
@permission_required('cms.manage_pois', raise_exception=True)
def archive_poi(request, poi_id, region_slug, language_code):
    poi = POI.objects.get(id=poi_id)

    poi.public = False
    poi.archived = True
    poi.save()

    messages.success(request, _('POI was successfully archived.'))

    return redirect('pois', **{
                'region_slug': region_slug,
                'language_code': language_code,
    })


@login_required
@region_permission_required
@permission_required('cms.manage_pois', raise_exception=True)
def restore_poi(request, poi_id, region_slug, language_code):
    poi = POI.objects.get(id=poi_id)

    poi.archived = False
    poi.save()

    messages.success(request, _('POI was successfully restored.'))

    return redirect('pois', **{
                'region_slug': region_slug,
                'language_code': language_code,
    })


@login_required
@region_permission_required
@permission_required('cms.manage_pois', raise_exception=True)
def view_poi(request, poi_id, region_slug, language_code):
    template_name = 'pois/poi_view.html'
    poi = POI.objects.get(id=poi_id)

    poi_translation = poi.get_translation(language_code)

    if not poi_translation:
        raise Http404

    return render(
        request,
        template_name,
        {
            "poi_translation": poi_translation
        }
    )
