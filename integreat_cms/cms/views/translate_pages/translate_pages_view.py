import logging

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import PageFilterForm
from ..mixins import SummAiContextMixin
from ...models import Page

from ...constants import translation_status

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_page"), name="dispatch")
class TranslatePagesView(TemplateView, SummAiContextMixin):
    """
    View for showing the page tree translations
    """

    #: Template for list of non-archived pages
    template = "translate_pages/translate_pages_tree.html"
    #: Whether or not to show archived pages
    archived = False

    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "translate_pages"}

    def get(self, request, *args, **kwargs):
        r"""
        Render page tree

        :param request: The current request
        :type request: ~django.http.HttpRequest

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
                "translate_pages",
                **{
                    "region_slug": region.slug,
                    "language_slug": region.default_language.slug,
                },
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
                },
            )

        if not request.user.has_perm("cms.manage_translations"):
            access_granted_pages = Page.objects.filter(
                Q(editors=request.user) | Q(publishers=request.user)
            ).filter(region=request.region)
            if request.user.organization:
                access_granted_pages = access_granted_pages.union(
                    Page.objects.filter(organization=request.user.organization)
                )
            else:
                messages.warning(
                    request, _("You don't have the permission to manage translations.")
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
            archived=None
        )
        # Filter pages according to given filters, if any
        pages = filter_form.apply(pages, language_slug)
        languages = list(region.active_languages)
        languages_to_translate = list(
            filter(lambda l: l.id != region.default_language.id, languages)
        )

        return render(
            request,
            self.template,
            {
                **self.get_context_data(**kwargs),
                "t_languages": str(languages),
                "translation_status": translation_status,
                "pages": pages,
                "language": language,
                "languages": languages,
                "languages_to_translate": languages_to_translate,
                "filter_form": filter_form,
                "XLIFF_EXPORT_VERSION": settings.XLIFF_EXPORT_VERSION,
            },
        )
