"""
This module contains view actions for the language tree.
Typically, they do not render a whole page, but only parts of it or they redirect to regular views.
"""
import logging

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.db import transaction

from treebeard.exceptions import InvalidPosition, InvalidMoveToDescendant
from cacheops import invalidate_obj

from ...constants import position
from ...decorators import permission_required
from ...models import LanguageTreeNode

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_languagetreenode")
@transaction.atomic
def move_language_tree_node(request, region_slug, pk, target_id, target_position):
    """
    This action moves the given language tree node to the given position relative to the given target.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the region which language tree should be modified
    :type region_slug: str

    :param pk: The id of the language tree node which should be moved
    :type pk: int

    :param target_id: The id of the target language tree node
    :type target_id: int

    :param target_position: The desired position (choices: :mod:`~integreat_cms.cms.constants.position`)
    :type target_position: str

    :return: A redirection to the language tree
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = request.region
    language_tree_node = get_object_or_404(region.language_tree_nodes, id=pk)
    target = get_object_or_404(region.language_tree_nodes, id=target_id)

    try:
        if target.depth == 1 and target_position in [position.LEFT, position.RIGHT]:
            raise InvalidPosition(_("A region can only have one root language."))
        language_tree_node.move(target, target_position)
        # Call the save method on the (reloaded) node in order to trigger possible signal handlers etc.
        # (The move()-method executes raw sql which might cause problems if the instance isn't fetched again)
        language_tree_node = LanguageTreeNode.objects.get(id=pk)
        language_tree_node.save()
        manually_invalidate_models(region)
        messages.success(
            request,
            _('The language tree node "{}" was successfully moved.').format(
                language_tree_node.translated_name
            ),
        )
        logger.debug(
            "%r moved to %r of %r by %r",
            language_tree_node,
            target_position,
            target,
            request.user,
        )
    except (ValueError, InvalidPosition, InvalidMoveToDescendant) as e:
        messages.error(request, e)
        logger.exception(e)

    return redirect("languagetreenodes", **{"region_slug": region_slug})


@require_POST
@permission_required("cms.delete_languagetreenode")
@transaction.atomic
def delete_language_tree_node(request, region_slug, pk):
    """
    Deletes the language node of distinct region
    and all page translations for this language

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the region which language node should be deleted
    :type region_slug: str

    :param pk: The id of the language tree node which should be deleted
    :type pk: int

    :return: A redirection to the language tree
    :rtype: ~django.http.HttpResponseRedirect
    """
    # get current region
    region = request.region
    # get current selected language node
    language_node = get_object_or_404(region.language_tree_nodes, id=pk)
    # get all page translation assigned to the language node
    page_translations = language_node.language.page_translations
    # filter those translation that belong to the region and delete them
    page_translations.filter(page__region=region).delete()
    # get all event translation assigned to the language node
    event_translations = language_node.language.event_translations
    # filter those translation that belong to the region and delete them
    event_translations.filter(event__region=region).delete()
    # get all poi translation assigned to the language node
    poi_translations = language_node.language.poi_translations
    # filter those translation that belong to the region and delete them
    poi_translations.filter(poi__region=region).delete()
    # get all push notification translation assigned to the language node
    push_notification_translations = (
        language_node.language.push_notification_translations
    )
    # filter those translation that belong to the region and delete them
    push_notification_translations.filter(push_notification__region=region).delete()

    logger.debug("%r deleted by %r", language_node, request.user)
    language_node.delete()

    manually_invalidate_models(region)

    messages.success(
        request,
        _(
            'The language tree node "{}" and all corresponding translations were successfully deleted.'
        ).format(language_node.translated_name),
    )
    return redirect("languagetreenodes", **{"region_slug": region_slug})


def manually_invalidate_models(region):
    """
    This is a helper function to iterate through all affected objects and invalidate their cache.
    This is necessary as the original cache invalidation of cacheops only triggers for direct foreign key relationships.

    :param region: The affected region
    :type region: ~integreat_cms.cms.models.regions.region.Region
    """
    for page in region.pages.all():
        invalidate_obj(page)
    for event in region.events.all():
        invalidate_obj(event)
    for poi in region.pois.all():
        invalidate_obj(poi)
    for push_notification in region.push_notifications.all():
        invalidate_obj(push_notification)
