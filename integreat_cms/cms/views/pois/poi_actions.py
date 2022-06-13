"""
This module contains view actions for objects related to POIs.
"""
import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from linkcheck.models import Link

from ...decorators import permission_required
from ...models import POI

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_poi")
def archive_poi(request, poi_id, region_slug, language_slug):
    """
    Archive POI object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param poi_id: The id of the POI which should be archived
    :type poi_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    :rtype: ~django.http.HttpResponseRedirect
    """
    poi = POI.objects.get(id=poi_id)

    poi.archived = True
    poi.save()

    # Delete related link objects as they are no longer required
    Link.objects.filter(poi_translation__poi=poi).delete()

    logger.debug("%r archived by %r", poi, request.user)
    messages.success(request, _("Location was successfully archived"))

    return redirect(
        "pois",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        }
    )


@require_POST
@permission_required("cms.change_poi")
def restore_poi(request, poi_id, region_slug, language_slug):
    """
    Restore POI object (set ``archived=False``)

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param poi_id: The id of the POI which should be restored
    :type poi_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    :rtype: ~django.http.HttpResponseRedirect
    """
    poi = POI.objects.get(id=poi_id)

    poi.archived = False
    poi.save()

    # Restore related link objects
    for translation in poi.translations.distinct("poi__pk", "language__pk"):
        # The post_save signal will create link objects from the content
        translation.save(update_timestamp=False)

    logger.debug("%r restored by %r", poi, request.user)
    messages.success(request, _("Location was successfully restored"))

    return redirect(
        "pois",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        }
    )


@require_POST
@permission_required("cms.delete_poi")
def delete_poi(request, poi_id, region_slug, language_slug):
    """
    Delete POI object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param poi_id: The id of the POI which should be deleted
    :type poi_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    poi = POI.objects.get(id=poi_id)
    logger.debug("%r deleted by %r", poi, request.user)
    poi.delete()
    messages.success(request, _("Location was successfully deleted"))

    return redirect(
        "pois",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        }
    )


@permission_required("cms.view_poi")
# pylint: disable=unused-argument
def view_poi(request, poi_id, region_slug, language_slug):
    """
    View POI object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param poi_id: The id of the POI which should be viewed
    :type poi_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :raises ~django.http.Http404: If user no translation exists for the requested POI and language

    :return: A redirection to the :class:`~integreat_cms.cms.views.pois.poi_list_view.POIListView`
    :rtype: ~django.http.HttpResponseRedirect
    """
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pois/poi_view.html"
    poi = POI.objects.get(id=poi_id)

    poi_translation = poi.get_translation(language_slug)

    if not poi_translation:
        raise Http404

    return render(request, template_name, {"poi_translation": poi_translation})
