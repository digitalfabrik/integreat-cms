"""
This module contains mixins for our views
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin

from ...core.utils.machine_translation_provider import MachineTranslationProvider

if TYPE_CHECKING:
    from typing import Any

    from django.core.paginator import Page
    from django.db.models.query import QuerySet

    from ..forms import ObjectSearchForm


class RegionPermissionRequiredMixing(UserPassesTestMixin):
    """
    A mixin that can be used for class-based views that require that the user is has access to the current region of this request
    """

    def test_func(self) -> bool:
        """
        The test this account has to pass

        :return: Whether this account has passed the test
        """
        # Superusers and staff have permissions for all regions
        return (
            self.request.user.is_superuser
            or self.request.user.is_staff
            or self.request.region in self.request.user.regions.all()
        )


class ModelTemplateResponseMixin(TemplateResponseMixin):
    """
    A mixin that can be used to render a template of a model (e.g. list or form)
    """

    @property
    def template_name(self) -> str:
        """
        Return the template name to be used for the request.

        :return: The template to be rendered
        """
        model_name = self.model._meta.model_name
        model_name_plural = self.model.get_model_name_plural()
        return f"{model_name_plural}/{model_name}{self.template_name_suffix}.html"


class ModelConfirmationContextMixin(ContextMixin):
    """
    A mixin that can be used to inject confirmation text into a template of a model (e.g. list or form)
    """

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this {}",
                ).format(self.model._meta.verbose_name),
                "delete_dialog_text": _("This cannot be reversed."),
            },
        )
        return context


class ContentEditLockMixin(ContextMixin):
    """
    A mixin that provides some variables required for the content edit lock
    """

    #: The reverse name of the url of the associated list view
    back_url_name: str | None = None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "back_url": reverse(
                    self.back_url_name,
                    kwargs={
                        "region_slug": kwargs["region_slug"],
                        "language_slug": kwargs["language_slug"],
                    },
                ),
            },
        )
        return context


class MachineTranslationContextMixin(ContextMixin):
    """
    This mixin provides extra context for machine translation options
    """

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        language_slug = kwargs["language_slug"]
        language_node = self.request.region.language_node_by_slug[language_slug]
        context["MT_PROVIDER"] = language_node.mt_provider
        context["MT_PERMITTED"] = (
            MachineTranslationProvider.is_permitted(
                self.request.region,
                self.request.user,
                self.translation_model,
            )
            and not language_node.is_root()
            and not (
                language_node.mt_provider
                and language_node.mt_provider.bulk_only_for_staff
                and not self.request.user.is_staff
            )
        )
        return context


class PaginationMixin:
    """
    Mixin to add pagination to a view.
    The number of the page to view can be given by the ``page`` parameter in the request.
    The page size can be defined by a ``size`` parameter in the request.
    If no size is set explicitly, the page size is given by the ``PER_PAGE` setting,
    and the fallback page size value is 10.
    Note that this mixin is intended for extending Django's View class (or child classes),
    and expects a ``self.request`` attribute. Django's generic View defines the request attribute
    in the dispatch phase.
    """

    request: Any
    default_page_size: int = settings.PER_PAGE or 10
    max_page_size: int = 100

    def paginate_queryset(self, queryset: QuerySet) -> Page:
        page = self.request.GET.get("page", 1)
        size = self.request.GET.get("size", self.default_page_size)

        try:
            size = min(int(size), self.max_page_size)
        except (TypeError, ValueError):
            size = self.default_page_size

        paginator = Paginator(queryset, size)
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return page_obj


class FilterSortMixin:
    """
    Mixin to add filtering and sorting to a view.
    Filtering logic is handled by the SearchForm. To add filtering to a view,
    set a ``filter_form_class` attribute (the ``filter_form_class`` should be a child of
    :class:`~integreat_cms.cms.forms.object_search_form.ObjectSearchForm`).
    To allow sorting, add a ``sort_fields`` list attribute to your view.
    Note that this mixin is intended for extending Django's View class (or child classes),
    and expects a ``self.request`` attribute. Django's generic View defines the request attribute
    in the dispatch phase.
    """

    request: Any
    filter_form_class: type[ObjectSearchForm] | None = None
    sort_fields: list[str] = []

    def get_filter_form(self) -> ObjectSearchForm | None:
        if self.filter_form_class is None:
            return None
        return self.filter_form_class(self.request.POST or None)

    def get_filtered_sorted_queryset(self, queryset: QuerySet) -> QuerySet:
        form = self.get_filter_form()
        if form and form.is_valid():
            queryset = form.apply_filters(queryset)

        order_by = [
            f
            for f in self.request.POST.get("sort", "").split(",")
            if f.lstrip("-") in self.sort_fields
        ]
        return queryset.order_by(*order_by)
