import logging

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import translation_status
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

        # Filter pages according to given filters, if any
        filter_data = kwargs.get("filter_data")

        if filter_data or self.archived:
            page_queryset = region.pages.all()
        else:
            page_queryset = region.pages.filter(lft=1)
        pages = page_queryset.prefetch_major_public_translations().cache_tree(
            archived=self.archived
        )

        if filter_data:
            # Set data for filter form rendering
            filter_form = PageFilterForm(data=filter_data)
            pages = self.filter_pages(pages, language_slug, filter_form)
        else:
            filter_form = PageFilterForm()
            filter_form.changed_data.clear()

        response = render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "pages": pages,
                "language": language,
                "languages": region.active_languages,
                "filter_form": filter_form,
            },
        )
        # Disable browser cache of page tree to prevent subpages from being expanded after using "back"-button
        response["Cache-Control"] = "no-store, must-revalidate"
        return response

    def post(self, request, *args, **kwargs):
        r"""
        Apply page filters and render page tree

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return self.get(request, *args, **kwargs, filter_data=request.POST)

    @staticmethod
    def filter_pages(pages, language_slug, filter_form):
        """
        Filter the pages list according to the given filter data

        :param pages: The list of pages
        :type pages: list

        :param language_slug: The slug of the current language
        :type language_slug: str

        :param filter_form: The filter form
        :type filter_form: integreat_cms.cms.forms.pages.page_filter_form.PageFilterForm

        :return: The filtered page list
        :rtype: list
        """
        if filter_form.is_valid():
            query = filter_form.cleaned_data["query"]
            if query:
                # Buffer variable because the pages list should not be modified during iteration
                filtered_pages = []
                for page in pages:
                    translation = page.get_translation(language_slug)
                    if translation and (
                        query.lower() in translation.slug
                        or query.lower() in translation.title.lower()
                    ):
                        filtered_pages.append(page)
                pages = filtered_pages

            selected_status = filter_form.cleaned_data["translation_status"]
            # Only filter if at least one checkbox but not all are checked
            if 0 < len(selected_status) < len(translation_status.CHOICES):
                # Buffer variable because the pages list should not be modified during iteration
                filtered_pages = []
                for page in pages:
                    translation_state = page.translation_states.get(language_slug)
                    if translation_state and translation_state[1] in selected_status:
                        filtered_pages.append(page)
                pages = filtered_pages
        return pages
