from __future__ import annotations

import json
from ast import literal_eval
from collections import defaultdict

from django.http import HttpRequest, JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import get_language
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...models.languages.language import Language
from ..pages.page_context_mixin import PageContextMixin


@permission_required("cms.view_page")
@require_POST
# pylint: disable=unused-argument, too-many-locals
def render_partial_page_tree_views(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    is_archive: str,
    is_statistics: str,
) -> JsonResponse:
    r"""
    Retrieve the rendered subtree of a given root page

    :param request: The current request
    :param language_slug: The slug of the current language
    :param is_archive: True when only archive pages are requested, False otherwise
    :param is_statistics: True when this page tree is for statistics, if for pages it's False
    :return: The rendered template responses
    """
    requested_tree_ids = [int(i) for i in json.loads(request.body.decode("utf-8"))]

    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    # Convert is_archive from String to Boolean
    is_archive = literal_eval(is_archive)

    # Convert is_statistics from String to Boolean
    is_statistics = literal_eval(is_statistics)

    if is_statistics:
        row_template = "statistics/statistics_viewed_pages_node.html"
    if not is_statistics and not is_archive:
        row_template = "pages/pages_page_tree_node.html"

    backend_language = Language.objects.filter(slug=get_language()).first()

    all_pages = (
        region.pages.filter(tree_id__in=requested_tree_ids)
        .prefetch_major_translations()
        .prefetch_related("mirroring_pages")
        .cache_tree(archived=is_archive)
    )

    pages_by_id = defaultdict(list)
    for page in all_pages:
        pages_by_id[page.tree_id].append(page)

    sub_trees = []
    for tree_id in requested_tree_ids:
        # Skip page trees which do not exist
        if tree_id not in pages_by_id:
            continue
        # Get the tree of the given id
        pages = pages_by_id[tree_id]
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
                    "is_archive": is_archive,
                    "is_statistics": is_statistics,
                    "row_template": row_template,
                },
                request,
            ),
        )

    return JsonResponse({"data": sub_trees})
