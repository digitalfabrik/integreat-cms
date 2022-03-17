import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import PageFilterForm
from .page_context_mixin import PageContextMixin

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PageTreeView(TemplateView, PageContextMixin):
    """
    View for showing the page tree
    """

    #: Template for list of non-archived pages
    template = "pages/page_tree.html"
    #: Template for list of archived pages
    template_archived = "pages/page_tree_archived.html"
    #: Whether or not to show archived pages
    archived = False

    @property
    def template_name(self):
        """
        Select correct HTML template, depending on :attr:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        :rtype: str
        """

        return self.template_archived if self.archived else self.template

    def get(self, request, *args, **kwargs):
        r"""
        Render page tree

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        # current region
        region = request.region

        # current language
        language_slug = kwargs.get("language_slug")
        if language_slug:
            language = region.get_language_or_404(language_slug, only_active=True)
        elif region.default_language:
            return redirect(
                "pages",
                **{
                    "region_slug": region.slug,
                    "language_slug": region.default_language.slug,
                }
            )
        else:
            messages.error(
                request,
                _("Please create at least one language node before creating pages."),
            )
            return redirect(
                "language_tree",
                **{
                    "region_slug": region.slug,
                }
            )

        if not request.user.has_perm("cms.change_page"):
            messages.warning(
                request, _("You don't have the permission to edit or create pages.")
            )

        # Initialize page filter form
        filter_form = PageFilterForm(data=request.GET)

        if filter_form.is_enabled or self.archived:
            # If filters are applied or only archived pages are requested, fetch all elements from the database
            page_queryset = region.pages.all()
        else:
            # Else, only fetch the root pages and load the subpages dynamically via ajax
            page_queryset = region.pages.filter(lft=1)

        # Cache tree structure to reduce database queries
        pages = page_queryset.prefetch_major_public_translations().cache_tree(
            archived=self.archived
        )

        # Filter pages according to given filters, if any
        pages = filter_form.apply(pages, language_slug)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "pages": pages,
                "language": language,
                "languages": region.active_languages,
                "filter_form": filter_form,
                "XLIFF_EXPORT_VERSION": settings.XLIFF_EXPORT_VERSION,
            },
        )
