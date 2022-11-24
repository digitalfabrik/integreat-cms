"""
This module contains view actions for region objects.
"""
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...models import Region, Page

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.delete_region")
# pylint: disable=unused-argument
def delete_region(request, *args, **kwargs):
    r"""
    This view deletes a region. All content is cascade deleted. Region users, who are not assigned to any other region,
    are manually removed.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param \*args: The supplied arguments
    :type \*args: list

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict

    :return: A redirection to the media library
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = get_object_or_404(Region, slug=kwargs.get("slug"))

    # Check whether region can be safely deleted
    mirrored_pages = Page.objects.filter(
        region=region, mirroring_pages__isnull=False
    ).distinct()
    if len(mirrored_pages) > 0:
        messages.error(
            request,
            format_html(
                "{}<ul class='list-disc pl-4'>{}</ul>",
                _(
                    "Region could not be deleted, because the following pages are mirrored in other regions:"
                ),
                format_html_join(
                    "\n",
                    "<li><a href='{}' class='underline hover:no-underline'>{}</a> ({} {})</li>",
                    [
                        (
                            page.best_translation.backend_edit_link,
                            page.best_translation.title,
                            _("is mirrored here:"),
                            format_html_join(
                                ", ",
                                "<a href='{}' class='underline hover:no-underline'>{}</a>",
                                [
                                    (
                                        mirrored_page.best_translation.backend_edit_link,
                                        mirrored_page.best_translation.title,
                                    )
                                    for mirrored_page in page.mirroring_pages.all()
                                ],
                            ),
                        )
                        for page in mirrored_pages
                    ],
                ),
            ),
        )
        return redirect(
            "edit_region",
            **{
                "slug": region.slug,
            },
        )

    # Remove hierarchy to prevent ProtectedError when children get deleted before their parents
    region.pages.update(parent=None)
    region.language_tree_nodes.update(parent=None)
    region.media_directories.update(parent=None)
    region.files.update(parent_directory=None)
    # Prevent ProtectedError when location gets deleted before their events
    region.events.update(location=None)
    # Delete region and cascade delete all contents
    deleted_objects = region.delete()
    logger.info(
        "%r deleted %r, cascade deleted objects: %r",
        request.user,
        region,
        deleted_objects,
    )
    # Get orphan users who aren't superuser or staff and don't have a region assigned
    # (Creating users with these combination is impossible, so they were region users of the deleted region before)
    orphan_users = get_user_model().objects.filter(
        is_superuser=False, is_staff=False, regions=None
    )
    if orphan_users.exists():
        logger.info(
            "Deleted orphan users: %r",
            orphan_users,
        )
        orphan_users.delete()

    messages.success(request, _("Region was successfully deleted"))

    return redirect("regions")
