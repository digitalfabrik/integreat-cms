"""
This module contains view actions for the language tree.
Typically, they do not render a whole page, but only parts of it or they redirect to regular views.
"""
import logging

from mptt.exceptions import InvalidMove

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from ...constants import position
from ...decorators import region_permission_required, permission_required
from ...models import Region

logger = logging.getLogger(__name__)


@require_POST
@login_required
@region_permission_required
@permission_required("cms.change_languagetreenode")
def move_language_tree_node(
    request, region_slug, language_tree_node_id, target_id, target_position
):
    """
    This action moves the given language tree node to the given position relative to the given target.

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the region which language tree should be modified
    :type region_slug: str

    :param language_tree_node_id: The id of the language tree node which should be moved
    :type language_tree_node_id: int

    :param target_id: The id of the target language tree node
    :type target_id: int

    :param target_position: The desired position (choices: :mod:`cms.constants.position`)
    :type target_position: str

    :return: A redirection to the language tree
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    language_tree_node = get_object_or_404(
        region.language_tree_nodes, id=language_tree_node_id
    )
    target = get_object_or_404(region.language_tree_nodes, id=target_id)

    try:
        if target.level == 0 and target_position in [position.LEFT, position.RIGHT]:
            raise InvalidMove(_("A region can only have one root language."))
        language_tree_node.move_to(target, target_position)
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
    except (ValueError, InvalidMove) as e:
        messages.error(request, e)
        logger.exception(e)

    return redirect("language_tree", **{"region_slug": region_slug})


@require_POST
@login_required
@region_permission_required
@permission_required("cms.delete_languagetreenode")
def delete_language_tree_node(request, region_slug, language_tree_node_id):
    """
    Deletes the language node of distinct region
    and all page translations for this language

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the region which language node should be deleted
    :type region_slug: str

    :param language_tree_node_id: The id of the language tree node which should be deleted
    :type language_tree_node_id: int

    :return: A redirection to the language tree
    :rtype: ~django.http.HttpResponseRedirect
    """
    # get current region
    region = Region.get_current_region(request)
    # get current selected language node
    language_node = get_object_or_404(
        region.language_tree_nodes, id=language_tree_node_id
    )
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
    messages.success(
        request,
        _(
            'The language tree node "{}" and all corresponding translations were successfully deleted.'
        ).format(language_node.translated_name),
    )
    return redirect("language_tree", **{"region_slug": region_slug})
