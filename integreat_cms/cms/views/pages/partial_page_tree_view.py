from django.db.models import Q
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from integreat_cms.cms.views.pages.page_context_mixin import PageContextMixin

from ...decorators import permission_required


@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PartialPageTreeView(TemplateView, PageContextMixin):
    """
    View for rendering a partial page tree
    """

    #: Template for a partial page tree
    template = "pages/_page_tree_children.html"

    # pylint: disable=unused-argument
    def get(self, request, *args, **kwargs):
        r"""
        Retrieve the rendered subtree of a given parent page

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        tree_id = int(kwargs.get("tree_id"))
        lft = int(kwargs.get("lft"))
        rgt = int(kwargs.get("rgt"))
        depth = int(kwargs.get("depth"))
        region = request.region
        language = region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )
        # List of all ancestors, the requested parent and all direct children
        pages = (
            region.pages.filter(
                # This condition queries the parent and all direct children
                Q(tree_id=tree_id, lft__range=(lft, rgt - 1), depth__lte=depth + 1)
                # This condition queries all ancestors
                | Q(tree_id=tree_id, lft__lt=lft, rgt__gt=rgt)
            )
            .prefetch_major_public_translations()
            .cache_tree(False)
        )
        # If the depth is 1, the first element must be the direct parent, etc.
        parent = pages[depth - 1]
        # The remaining pages are the direct children
        children = pages[depth:]
        # For every depth level, exactly one ancestor is in the list
        ancestor_ids = [ancestor.id for ancestor in pages[:depth]]
        return render(
            request,
            self.template,
            {
                **self.get_context_data(**kwargs),
                "pages": children,
                "ancestor_ids": ancestor_ids,
                "language": language,
                "languages": region.active_languages,
                "parent_id": parent.id,
            },
        )
