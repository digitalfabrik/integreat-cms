from __future__ import annotations

import json
from collections import defaultdict

from django.http import HttpRequest, JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import get_language
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...models import Page
from ...models.languages.language import Language
from ..pages.page_context_mixin import PageContextMixin


@permission_required("cms.view_page")
@require_POST
# pylint: disable=unused-argument
def render_partial_page_tree_views(
    request: HttpRequest, region_slug: str, language_slug: str
) -> JsonResponse:
    r"""
    Retrieve the rendered subtree of a given root page

    :param request: The current request
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :return: The rendered template responses
    """
    requested_page_ids = [int(i) for i in json.loads(request.body.decode("utf-8"))]

    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    backend_language = Language.objects.filter(slug=get_language()).first()

    # all_pages = (
    #     region.pages.filter(tree_id__in=requested_tree_ids)
    #     .prefetch_major_translations()
    #     .prefetch_related("mirroring_pages")
    #     .cache_tree(archived=False)
    # )
    #
    # pages_by_id = defaultdict(list)
    # for page in all_pages:
    #     pages_by_id[page.tree_id].append(page)

    pages_by_id = {}
    for page_id in requested_page_ids:
        if page := Page.objects.filter(id=page_id).first():
            pages_by_id[page_id] = list(
                region.pages.filter(lft__gte=page.lft, rgt__lte=page.rgt)
            )

    sub_trees = []
    for page_id in requested_page_ids:
        # Skip page trees which do not exist
        if page_id not in pages_by_id:
            continue
        # Get the tree of the given id
        pages = pages_by_id[page_id]
        # The first element must be the root node
        parent = pages[0]
        # The remaining pages are the descendants
        children = pages[1:]
        sub_trees.append(
            render_to_string(
                "pages/_page_tree_children.html",
                {
                    **PageContextMixin().get_context_data(),
                    "backend_language": backend_language,
                    "pages": children,
                    "language": language,
                    "languages": region.active_languages,
                    "parent_id": parent.id,
                },
                request,
            )
        )

    return JsonResponse({"data": sub_trees})
