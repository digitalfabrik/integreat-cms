"""

Returns:
    [type]: [description]
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import region_permission_required
from ...forms.pages import PageForm, PageTranslationForm
from ...models import Page, PageTranslation, Region, Language

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class PageView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.view_pages"
    raise_exception = True

    template_name = "pages/page_form.html"
    base_context = {"current_menu_item": "pages", "PUBLIC": status.PUBLIC}

    def get(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get("region_slug"))

        language = Language.objects.get(code=kwargs.get("language_code"))

        # get page and translation objects if they exist
        page = Page.objects.filter(id=kwargs.get("page_id")).first()
        page_translation = PageTranslation.objects.filter(
            page=page,
            language=language,
        ).first()

        # Make form disabled if user has no permission to edit the page
        disabled = False
        if page:
            if page.archived:
                disabled = True
                messages.warning(
                    request, _("You cannot edit this page because it is archived.")
                )
            elif not request.user.has_perm("cms.edit_page", page):
                disabled = True
                messages.warning(
                    request,
                    _(
                        "You don't have the permission to edit this page, but you can propose changes and submit them for review instead."
                    ),
                )
        else:
            if not request.user.has_perm("cms.edit_pages"):
                raise PermissionDenied

        page_form = PageForm(
            instance=page, region=region, language=language, disabled=disabled
        )
        page_translation_form = PageTranslationForm(
            instance=page_translation, disabled=disabled
        )

        # Pass side by side language options
        side_by_side_language_options = self.get_side_by_side_language_options(
            region, language, page
        )

        # Pass siblings to template to enable rendering of page order table
        if not page or not page.parent:
            siblings = Page.objects.filter(level=0, region=region)
        else:
            siblings = page.parent.children.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "page_form": page_form,
                "page_translation_form": page_translation_form,
                "page": page,
                "siblings": siblings,
                "language": language,
                # Languages for tab view
                "languages": region.languages if page else [language],
                "side_by_side_language_options": side_by_side_language_options,
            },
        )

    # pylint: disable=too-many-branches,unused-argument
    def post(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get("region_slug"))
        language = Language.objects.get(code=kwargs.get("language_code"))

        page_instance = Page.objects.filter(id=kwargs.get("page_id")).first()
        page_translation_instance = PageTranslation.objects.filter(
            page=page_instance,
            language=language,
        ).first()

        # Pass siblings to template to enable rendering of page order table
        if not page_instance or not page_instance.parent:
            siblings = Page.objects.filter(level=0, region=region)
        else:
            siblings = page_instance.parent.children.all()

        if not request.user.has_perm("cms.edit_page", page_instance):
            raise PermissionDenied

        page_form = PageForm(
            request.POST,
            instance=page_instance,
            region=region,
            language=language,
        )
        page_translation_form = PageTranslationForm(
            request.POST,
            instance=page_translation_instance,
            region=region,
            language=language,
        )

        if (
            page_translation_form.data.get("public")
            and "public" in page_translation_form.changed_data
        ):
            if not request.user.has_perm("cms.publish_page", page_instance):
                raise PermissionDenied

        side_by_side_language_options = self.get_side_by_side_language_options(
            region, language, page_instance
        )

        # TODO: error handling
        if not page_form.is_valid() or not page_translation_form.is_valid():
            messages.error(request, _("Errors have occurred."))
            return render(
                request,
                self.template_name,
                {
                    **self.base_context,
                    "page_form": page_form,
                    "page_translation_form": page_translation_form,
                    "page": page_instance,
                    "siblings": siblings,
                    "language": language,
                    # Languages for tab view
                    "languages": region.languages if page_instance else [language],
                    "side_by_side_language_options": side_by_side_language_options,
                },
            )

        if not page_form.has_changed() and not page_translation_form.has_changed():
            messages.info(request, _("No changes detected."))
            return render(
                request,
                self.template_name,
                {
                    **self.base_context,
                    "page_form": page_form,
                    "page_translation_form": page_translation_form,
                    "page": page_instance,
                    "siblings": siblings,
                    "language": language,
                    # Languages for tab view
                    "languages": region.languages if page_instance else [language],
                    "side_by_side_language_options": side_by_side_language_options,
                },
            )

        page = page_form.save()
        page_translation = page_translation_form.save(
            page=page,
            user=request.user,
        )

        published = page_translation.status == status.PUBLIC
        if not page_instance:
            if published:
                messages.success(
                    request, _("Page was successfully created and published.")
                )
            else:
                messages.success(request, _("Page was successfully created."))
        elif not page_translation_instance:
            if published:
                messages.success(
                    request, _("Translation was successfully created and published.")
                )
            else:
                messages.success(request, _("Translation was successfully created."))
        else:
            if published:
                messages.success(request, _("Translation was successfully published."))
            else:
                messages.success(request, _("Translation was successfully saved."))

        return redirect(
            "edit_page",
            **{
                "page_id": page.id,
                "region_slug": region.slug,
                "language_code": language.code,
            },
        )

    @staticmethod
    def get_side_by_side_language_options(region, language, page):
        """
        This is a helper function to generate the side-by-side langauge options for both the get and post requests.

        :param region: The current region
        :type region: ~cms.models.regions.region.Region

        :param language: The current language
        :type language: ~cms.models.languages.language.Language

        :param page: The current page
        :type page: ~cms.models.pages.page.Page

        :return: The list of language options, each represented by a dict
        :rtype: list
        """
        side_by_side_language_options = []
        for language_node in region.language_tree_nodes.all():
            if language_node.parent:
                source_translation = PageTranslation.objects.filter(
                    page=page,
                    language=language_node.parent.language,
                )
                side_by_side_language_options.append(
                    {
                        "value": language_node.language.code,
                        "label": _("{source_language} to {target_language}").format(
                            source_language=language_node.parent.language.translated_name,
                            target_language=language_node.language.translated_name,
                        ),
                        "selected": language_node.language == language,
                        "disabled": not source_translation.exists(),
                    }
                )
        return side_by_side_language_options
