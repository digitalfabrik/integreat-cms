"""
This module contains view actions for the language tree.
Typically, they do not render a whole page, but only parts of it or they redirect to regular views.

.. warning::
    Any action modifying the database with treebeard should use ``@tree_mutex(MODEL_NAME)`` from ``integreat_cms.cms.utils.tree_mutex``
    as a decorator instead of ``@transaction.atomic`` to force treebeard to actually use transactions.
    Otherwise, the data WILL get corrupted during concurrent treebeard calls!
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from treebeard.exceptions import InvalidMoveToDescendant, InvalidPosition

from ...constants import position
from ...decorators import permission_required
from ...models import LanguageTreeNode
from ...utils.tree_mutex import tree_mutex

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect


logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_languagetreenode")
@tree_mutex("languagetreenode")
def move_language_tree_node(
    request: HttpRequest,
    region_slug: str,
    pk: int,
    target_id: int,
    target_position: str,
) -> HttpResponseRedirect:
    """
    This action moves the given language tree node to the given position relative to the given target.

    :param request: The current request
    :param region_slug: The slug of the region which language tree should be modified
    :param pk: The id of the language tree node which should be moved
    :param target_id: The id of the target language tree node
    :param target_position: The desired position (choices: :mod:`~integreat_cms.cms.constants.position`)
    :return: A redirection to the language tree
    """

    region = request.region
    language_tree_node = get_object_or_404(region.language_tree_nodes, id=pk)
    target = get_object_or_404(region.language_tree_nodes, id=target_id)

    try:
        if target.depth == 1 and target_position in [position.LEFT, position.RIGHT]:
            raise InvalidPosition(_("A region can only have one root language."))  # noqa: TRY301
        language_tree_node.move(target, target_position)
        # Call the save method on the (reloaded) node in order to trigger possible signal handlers etc.
        # (The move()-method executes raw sql which might cause problems if the instance isn't fetched again)
        language_tree_node = LanguageTreeNode.objects.get(id=pk)
        language_tree_node.save()
        language_tree_node.manually_invalidate_models(region)
        messages.success(
            request,
            _('The language tree node "{}" was successfully moved.').format(
                language_tree_node.translated_name,
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
        logger.exception("")

    return redirect("languagetreenodes", **{"region_slug": region_slug})


@require_POST
@permission_required("cms.delete_languagetreenode")
@tree_mutex("languagetreenode")
def delete_language_tree_node(
    request: HttpRequest,
    region_slug: str,
    pk: int,
) -> HttpResponseRedirect:
    """
    Deletes the language node of distinct region
    and all page translations for this language

    :param request: The current request
    :param region_slug: The slug of the region which language node should be deleted
    :param pk: The id of the language tree node which should be deleted
    :return: A redirection to the language tree
    """
    # get current region
    region = request.region
    # get current selected language node
    language_node = get_object_or_404(region.language_tree_nodes, id=pk)

    can_delete, error_msg = language_node.can_be_deleted()
    if can_delete:
        try:
            language_node.delete()
        except ProtectedError:
            messages.error(
                request,
                _(
                    'The language tree node "{model_name}" cannot be deleted because it is the source language of other language(s).',
                ).format(model_name=language_node.translated_name),
            )
            return redirect("languagetreenodes", **{"region_slug": region_slug})
    else:
        messages.error(
            request,
            _(
                'The language tree node "{model_name}" cannot be deleted because {failure_reason}',
            ).format(
                model_name=language_node.translated_name, failure_reason=error_msg
            ),
        )
        return redirect("languagetreenodes", **{"region_slug": region_slug})

    language_node.manually_invalidate_models(region)
    messages.success(
        request,
        _(
            'The language tree node "{model_name}" and all corresponding translations were successfully deleted.',
        ).format(model_name=language_node.translated_name),
    )
    return redirect("languagetreenodes", **{"region_slug": region_slug})
