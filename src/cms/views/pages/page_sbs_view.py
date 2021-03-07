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
from ...forms import PageTranslationForm
from ...models import Region, Language


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class PageSideBySideView(PermissionRequiredMixin, TemplateView):
    """
    View for the page side by side form
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.view_pages"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pages/page_sbs.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "pages"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.pages.page_translation_form.PageTranslationForm` on the side by side view

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)
        page = region.pages.get(id=kwargs.get("page_id"))

        target_language = Language.objects.get(slug=kwargs.get("language_slug"))
        source_language_node = region.language_tree_nodes.get(
            language=target_language
        ).parent

        if source_language_node:
            source_language = source_language_node.language
        else:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view for the region's default language (in this case {default_language})."
                ).format(default_language=target_language.translated_name),
            )
            return redirect(
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                }
            )

        source_page_translation = page.get_translation(source_language.slug)
        target_page_translation = page.get_translation(target_language.slug)

        if not source_page_translation:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view if the source translation (in this case {source_language}) does not exist."
                ).format(source_language=source_language.translated_name),
            )
            return redirect(
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                }
            )

        page_translation_form = PageTranslationForm(
            instance=target_page_translation,
        )

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "page_translation_form": page_translation_form,
                "source_page_translation": source_page_translation,
                "target_language": target_language,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """
        Submit :class:`~cms.forms.pages.page_translation_form.PageTranslationForm` and save
        :class:`~cms.models.pages.page_translation.PageTranslation` object

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit pages

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)
        page = region.pages.get(id=kwargs.get("page_id"))

        if not request.user.has_perm("cms.edit_page", page):
            messages.warning(
                request,
                _("You don't have the permission to edit this page."),
            )
            raise PermissionDenied

        target_language = Language.objects.get(slug=kwargs.get("language_slug"))
        source_language_node = region.language_tree_nodes.get(
            language=target_language
        ).parent

        if source_language_node:
            source_page_translation = page.get_translation(
                source_language_node.language.slug
            )
        else:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view for the region's default language (in this case {default_language})."
                ).format(default_language=target_language.translated_name),
            )
            return redirect(
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                }
            )

        page_translation_instance = page.get_translation(target_language.slug)

        if not source_page_translation:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view if the source translation (in this case {source_language}) does not exist."
                ).format(source_language=source_language_node.language.translated_name),
            )
            return redirect(
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                }
            )

        page_translation_form = PageTranslationForm(
            request.POST,
            instance=page_translation_instance,
            region=region,
            language=target_language,
        )

        if not page_translation_form.is_valid():
            messages.error(request, _("Errors have occurred."))
        elif not page_translation_form.has_changed():
            messages.info(request, _("No changes detected."))
        else:
            page_translation = page_translation_form.save(page=page, user=request.user)
            published = page_translation.status == status.PUBLIC
            if not page_translation_instance:
                if published:
                    messages.success(
                        request,
                        _("Translation was successfully created and published"),
                    )
                else:
                    messages.success(request, _("Translation was successfully created"))
            else:
                if published:
                    messages.success(
                        request, _("Translation was successfully published")
                    )
                else:
                    messages.success(request, _("Translation was successfully saved"))

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "page_translation_form": page_translation_form,
                "source_page_translation": source_page_translation,
                "target_language": target_language,
            },
        )
