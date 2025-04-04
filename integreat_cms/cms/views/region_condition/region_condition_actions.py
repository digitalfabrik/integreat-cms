from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import magic
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from import_export import fields, resources
from tablib.formats import registry as format_registry

from ...constants import region_status
from ...models import Region
from ...utils.linkcheck_utils import filter_urls
from ..utils.hix import get_translation_under_hix_threshold

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

logger = logging.getLogger(__name__)


class RegionConditionResource(resources.ModelResource):
    """
    A resources class that connects to the django-import-export library.
    It represents the to-be exported status of all regions.
    """

    name = fields.Field(column_name=_("Region"))

    num_broken_links = fields.Field(column_name=_("Number of broken links"))

    num_low_hix_pages = fields.Field(column_name=_("Number of low hix pages"))

    num_pages = fields.Field(column_name=_("Number of pages"))

    num_pages_with_missing_or_outdated_translation = fields.Field(
        column_name=_(
            "Number of pages with at least one missing or outdated translation",
        ),
    )

    num_outdated_pages = fields.Field(column_name=_("Number of outdated pages"))

    has_translation_package_been_booked = fields.Field(
        column_name=_("Has translation package been booked?"),
        attribute="mt_addon_booked",
    )

    num_languages_besides_root_language = fields.Field(
        column_name=_("Number of active languages besides default language")
    )

    @staticmethod
    def dehydrate_name(region: Region) -> str:
        """
        :param region: The region
        :return: The name of a region
        """
        return f"{region.get_administrative_division_display()} {region.name}"

    @staticmethod
    def dehydrate_num_broken_links(region: Region) -> int:
        """
        :param region: The region
        :return: The number of broken links
        """
        _, count_dict = filter_urls(region_slug=region.slug)
        return count_dict["number_invalid_urls"]

    @staticmethod
    def dehydrate_num_low_hix_pages(region: Region) -> int:
        """
        :param region: The region
        :return: The number of page translations with low hix value
        """
        return get_translation_under_hix_threshold(region).count()

    @staticmethod
    def dehydrate_num_pages(region: Region) -> int:
        """
        :param region: The region
        :return: The number of pages in this region
        """
        return region.get_pages().count()

    @staticmethod
    def dehydrate_num_pages_with_missing_or_outdated_translation(region: Region) -> int:
        """
        :param region: The region
        :return: The number of pages with at least one missing or outdated translation
        """
        return region.get_partially_translated_pages()

    @staticmethod
    def dehydrate_num_outdated_pages(region: Region) -> int:
        """
        :param region: The region
        :return: The number of outdated pages
        """
        return region.outdated_pages().count()

    @staticmethod
    def dehydrate_num_languages_besides_root_language(region: Region) -> int:
        """
        :param region: The region
        :return: The number of languages besides the root language
        """
        return len(region.active_languages_without_default_language)

    def get_instance(self, *args: Any, **kwargs: Any) -> Any:
        """
        See :meth:`import_export.resources.Resource.get_instance`
        """
        return super().get_instance(*args, **kwargs)

    def import_data(self, *args: Any, **kwargs: Any) -> Any:
        """
        See :meth:`import_export.resources.Resource.import_data`
        """
        return super().import_data(*args, **kwargs)

    def import_row(self, *args: Any, **kwargs: Any) -> Any:
        """
        See :meth:`import_export.resources.Resource.import_row`
        """
        return super().import_row(*args, **kwargs)

    def save_instance(self, *args: Any, **kwargs: Any) -> Any:
        """
        See :meth:`import_export.resources.Resource.save_instance`
        """
        return super().save_instance(*args, **kwargs)

    class Meta:
        """
        Metaclass of the region status resource
        """

        model = Region
        # if we don't define the empty fields all fields are created in the default way additionally to our custom way
        fields = ()


@require_POST
@staff_member_required
def export_region_conditions(request: HttpRequest, file_format: str) -> HttpResponse:
    """
    Creates a data export summarizing the condition of all regions

    :param request: The current request
    :param file_format: The file format to export
    :return: A response containing the export data
    """
    resource = RegionConditionResource()
    dataset = resource.export(
        queryset=Region.objects.filter(
            Q(status=region_status.ACTIVE) | Q(status=region_status.HIDDEN),
        ).order_by("name"),
    )

    supported_file_formats = (f.title for f in format_registry.formats())
    if file_format not in supported_file_formats:
        raise ValueError(f"Unknown export format {file_format}")

    blob = getattr(dataset, file_format)
    mime = magic.from_buffer(blob, mime=True)
    response = HttpResponse(blob, content_type=mime)
    filename = f"region conditions summary {datetime.now().strftime('%Y-%m-%d %H:%M')}.{file_format}"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
