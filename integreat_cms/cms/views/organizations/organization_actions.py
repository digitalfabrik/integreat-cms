"""
This module contains action methods for organizations (archive, restore)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ...decorators import permission_required

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_organization")
def archive(
    request: HttpRequest,
    region_slug: str,
    organization_id: int,
) -> HttpResponseRedirect:
    """
    Set archived flag for an organization

    :param request: Object representing the user call
    :param region_slug: slug of the region to which an organization belongs
    :param organization_id: id of the event to be archived
    :return: The rendered template response
    """
    region = request.region
    organization = get_object_or_404(region.organizations, id=organization_id)

    if organization.archive():
        logger.debug("%r archived by %r", organization, request.user)
        messages.success(request, _("Organization was successfully archived"))
    else:
        logger.info("%r couldn't be archived by %r", organization, request.user)
        messages.error(
            request,
            _("Organization couldn't be archived as it's used by a page, poi or user"),
        )

    return redirect("organizations", region_slug=region_slug)


@require_POST
@permission_required("cms.change_organization")
def restore(
    request: HttpRequest,
    region_slug: str,
    organization_id: int,
) -> HttpResponseRedirect:
    """
    Remove archived flag for an organization

    :param request: Object representing the user call
    :param region_slug: slug of the region to which the organization belongs
    :param organization_id: id of the event to be restored
    :return: The rendered template response
    """
    region = request.region
    organization = get_object_or_404(region.organizations, id=organization_id)

    organization.restore()

    logger.debug("%r restored by %r", organization, request.user)
    messages.success(request, _("Organization was successfully restored"))

    return redirect("organizations", region_slug=region_slug)


@require_POST
@permission_required("cms.delete_organization")
def delete(
    request: HttpRequest,
    region_slug: str,
    organization_id: int,
) -> HttpResponseRedirect:
    """
    Delete a single organization

    :param request: Object representing the user call
    :param region_slug: slug of the region which the organization belongs to
    :param organization_id: id of the event to be deleted
    :return: The rendered template response
    """
    region = request.region
    organization = get_object_or_404(region.organizations, id=organization_id)

    if organization.delete():
        logger.info("%r deleted by %r", organization, request.user)
        messages.success(request, _("Organization was successfully deleted"))
    else:
        logger.info("%r couldn't be deleted by %r", organization, request.user)
        messages.error(
            request,
            _("Organization couldn't be deleted as it's used by a page, poi or user"),
        )

    return redirect("organizations", region_slug=region_slug)
