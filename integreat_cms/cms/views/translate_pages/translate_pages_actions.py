"""
This module contains view actions related to pages.
"""
import json
import logging
import os
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.db import transaction

from treebeard.exceptions import InvalidPosition, InvalidMoveToDescendant

from ....api.decorators import json_response
from ...constants import text_directions
from ...decorators import permission_required
from ...forms import PageForm
from ...models import Page, Region, PageTranslation
from ...utils.file_utils import extract_zip_archive

logger = logging.getLogger(__name__)



@require_POST
@permission_required("cms.manage_translations")
@transaction.atomic
def translate_page_by_machine(request, page_id, region_slug, language_slug, language):
    """
    Translate page to selected languages

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param page_id: The id of the page which should be deleted
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :param language: The target language 
    :type language_slug: int

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = request.region
    page = get_object_or_404(region.pages, id=page_id)

    # if page.children.exists():
    #     messages.error(request, _("You cannot delete a page which has subpages."))
    # elif page.mirroring_pages.exists():
    #     messages.error(
    #         request,
    #         _(
    #             "This page cannot be deleted because it was embedded as live content from another page."
    #         ),
    #     )
    # else:
    #     logger.info("%r deleted by %r", page, request.user)
    #     page.delete()
    #     messages.success(request, _("Page was successfully deleted"))

    # return redirect(
    #     "pages",
    #     **{
    #         "region_slug": region_slug,
    #         "language_slug": language_slug,
    #     },
    #)