from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView
from django.views.generic.base import ContextMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ModelFormMixin

from ...forms import poi_category_translation_formset_factory, POICategoryForm
from ...models import Language, POICategory
from ..delete_views import CustomDeleteView
from ..mixins import ModelTemplateResponseMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

    from integreat_cms.cms.forms.poi_categories.poi_category_translation_form import (
        BaseInlinePOICategoryTranslationFormSet,
    )

logger = logging.getLogger(__name__)


class POICategoryMixin(
    PermissionRequiredMixin,
    ModelTemplateResponseMixin,
    ModelFormMixin,
    SingleObjectMixin,
    ContextMixin,
):
    """
    This mixin handles views for POI categories
    """

    #: The model of this :class:`~django.views.generic.detail.SingleObjectMixin`
    #: (see :attr:`~django.views.generic.detail.SingleObjectMixin.model`)
    model = POICategory

    #: The object instance of this :class:`~django.views.generic.detail.SingleObjectMixin`
    #: (see :meth:`~django.views.generic.detail.SingleObjectMixin.get_object`)
    object: POICategory | None = None

    #: The context dict passed to the template
    #: (see :attr:`~django.views.generic.base.ContextMixin.extra_context`)
    extra_context = {"current_menu_item": "poicategories"}

    #: The formset of this mixin for POICategoryTranslation
    formset: BaseInlinePOICategoryTranslationFormSet | None = None

    #: The form class to instantiate
    form_class = POICategoryForm

    def get_permission_required(self) -> tuple[str]:
        """
        Override this method to override the permission_required attribute.

        :return: The permissions that are required for views inheriting from this Mixin
        """
        # If the form is submitted via POST, require the change permission
        if self.request.method == "POST":
            return ("cms.change_poicategory",)
        # If the form is just retrieved, require the view permission
        return ("cms.view_poicategory",)

    def get_formset(self) -> BaseInlinePOICategoryTranslationFormSet:
        """
        Retrieve and instantiate the formset class

        :returns: The formset
        """
        # If the formset already has been instantiated, don't do it again
        if self.formset:
            return self.formset
        # Get all languages
        languages = Language.objects.all()
        # If the formset is bound to a POICategory instance, only pass languages which do not yet have a translation
        if self.object:
            languages = languages.exclude(
                id__in=self.object.translations.values_list("language__id", flat=True)
            )
        # Get te formset class
        POICategoryTranslationFormSet = poi_category_translation_formset_factory()
        # Instantiate the formset
        return POICategoryTranslationFormSet(
            self.request.POST or None,
            instance=self.object,
            # Pass initial data for all languages which do not yet have a translation
            initial=[{"language": language} for language in languages],
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Add the formset to the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        context["formset"] = self.get_formset()
        return context

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Check whether the formset is valid and delegate to the respective function

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        form = self.get_form()
        self.formset = self.get_formset()

        if self.formset.is_valid() and form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def get_success_url(self) -> str:
        """
        Determine the URL to redirect to when the form is successfully validated

        :return: The url to redirect on success
        """
        if TYPE_CHECKING:
            assert self.object
        return reverse("edit_poicategory", kwargs={"pk": self.object.pk})

    def form_invalid(self, form: POICategoryForm) -> HttpResponseRedirect:
        """
        Renders a response, providing the invalid form as context.
        (see :meth:`~django.views.generic.edit.ModelFormMixin.form_invalid`)

        :param form: The invalid form instance
        :return: The rendered invalid form
        """
        if TYPE_CHECKING:
            assert self.formset
        # Add error messages
        for formset_form in self.formset:
            formset_form.add_error_messages(self.request)
        # Add non-field errors
        for error in self.formset.non_form_errors():
            messages.error(self.request, _(error))
        return super().form_invalid(form)


class POICategoryCreateView(POICategoryMixin, CreateView):
    """
    A view that displays a formset for creating a
    :class:`~integreat_cms.cms.models.poi_categories.poi_category.POICategory`
    object, redisplaying the form with validation errors
    (if there are any) and saving the object.
    """

    def form_valid(self, form: POICategoryForm) -> HttpResponseRedirect:
        """
        Create a :class:`~integreat_cms.cms.models.poi_categories.poi_category.POICategory`
        object and save all related
        :class:`~integreat_cms.cms.models.poi_categories.poi_category_translation.POICategoryTranslation`
        objects.
        (See :meth:`~django.views.generic.edit.ModelFormMixin.form_valid`)

        :param form: The valid form instance

        :return: A redirection to the success url
        """
        # Create POICategory object
        self.object = form.save(commit=False)
        if TYPE_CHECKING:
            assert self.object
            assert self.formset
        self.object.save()
        # Save POICategoryTranslation objects
        translations = self.formset.save(commit=False)
        for translation in translations:
            translation.category = self.object
            translation.save()
        messages.success(
            self.request,
            _('{} "{}" was successfully created').format(
                self.object._meta.verbose_name, self.object
            ),
        )
        return super().form_valid(form)


class POICategoryUpdateView(POICategoryMixin, UpdateView):
    """
    A view that displays a formset for editing an existing
    :class:`~integreat_cms.cms.models.poi_categories.poi_category.POICategory`
    object, redisplaying the formset with validation errors
    (if there are any) and saving changes to the object.
    This uses a form automatically generated from the object's model class.
    """

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Get the current :class:`~integreat_cms.cms.models.poi_categories.poi_category.POICategory`
        object and save the formset

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments

        :return: The redirect
        """
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: POICategoryForm) -> HttpResponseRedirect:
        """
        Save all changed
        :class:`~integreat_cms.cms.models.poi_categories.poi_category_translation.POICategoryTranslation`
        objects.
        (See :meth:`~django.views.generic.edit.ModelFormMixin.form_valid`)

        :param form: The valid form instance

        :return: A redirection to the success url
        """
        if TYPE_CHECKING:
            assert self.object
            assert self.formset
        if not self.formset.has_changed() and not form.has_changed():
            messages.info(self.request, _("No changes made"))
        else:
            self.formset.save()
            messages.success(
                self.request,
                _('{} "{}" was successfully saved').format(
                    self.object._meta.verbose_name, self.object
                ),
            )
        return super().form_valid(form)


class POICategoryDeleteView(CustomDeleteView):
    """
    A view that deletes an existing
    :class:`~integreat_cms.cms.models.poi_categories.poi_category.POICategory`
    object or adds a helpful message on failure and redirects back to the list view.
    """

    model = POICategory

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Attempt to delete the :class:`~integreat_cms.cms.models.poi_categories.poi_category.POICategory`
        object and add a helpful message and redirect back to the list view on failure.

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments

        :return: The redirect
        """
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                _(
                    "You cannot delete a location category that is used in at least one location."
                ),
            )
            return HttpResponseRedirect(reverse("poicategories"))
