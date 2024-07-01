from __future__ import annotations

import logging
from html import escape
from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.http import Http404
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils import timezone as django_timezone
from django.utils.functional import cached_property, keep_lazy_text
from django.utils.translation import gettext, override
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from datetime import datetime

    from django.db.models.query import QuerySet
    from django.utils.functional import Promise
    from django.utils.safestring import SafeString

    from ...nominatim_api.utils import BoundingBox
    from ..languages.language import Language
    from ..languages.language_tree_node import LanguageTreeNode
    from ..pages.imprint_page import ImprintPage
    from ..pages.page import PageQuerySet

from django.utils.safestring import mark_safe

from ....matomo_api.matomo_api_client import MatomoApiClient
from ....nominatim_api.utils import BoundingBox
from ...constants import (
    administrative_division,
    machine_translation_permissions,
    months,
    region_status,
)
from ...utils.translation_utils import gettext_many_lazy as __
from ..abstract_base_model import AbstractBaseModel
from ..offers.offer_template import OfferTemplate

logger = logging.getLogger(__name__)


@keep_lazy_text
def format_mt_help_text(help_text: Promise) -> str:
    """
    Helper function to lazily format help text with number separators

    :param help_text: MT field help text to format
    :return: formatted help text
    """
    return help_text.format(
        floatformat(settings.MT_CREDITS_ADDON, "g"),
        floatformat(settings.MT_CREDITS_FREE, "g"),
    )


# pylint: disable=too-few-public-methods
class RegionManager(models.Manager):
    """
    This manager annotates each region object with its language tree root node.
    This is done because it is required to calculate the region's
    :attr:`~integreat_cms.cms.models.regions.region.Region.default_language` which is called in
    :attr:`~integreat_cms.cms.models.regions.region.Region.full_name`.
    """

    def get_queryset(self) -> QuerySet:
        """
        Get the queryset of regions including the custom attribute ``language_tree_root`` which contains the root node
        of the region's language tree.

        :return: The queryset of regions
        """
        # Get model instead of importing it to avoid circular imports
        LanguageTreeNode = apps.get_model(
            app_label="cms", model_name="LanguageTreeNode"
        )
        return (
            super()
            .get_queryset()
            .prefetch_related(
                models.Prefetch(
                    "language_tree_nodes",
                    queryset=LanguageTreeNode.objects.all().select_related("language"),
                    to_attr="prefetched_language_tree_nodes",
                )
            )
        )


# pylint: disable=too-many-public-methods
class Region(AbstractBaseModel):
    """
    Data model representing region.
    """

    name = models.CharField(max_length=200, verbose_name=_("name"))
    #: See `community identification number <https://en.wikipedia.org/wiki/Community_Identification_Number>`__
    #: and `Gemeindeschlüssel (German) <https://de.wikipedia.org/wiki/Amtlicher_Gemeindeschl%C3%BCssel>`__
    common_id = models.CharField(
        max_length=48,
        blank=True,
        verbose_name=_("community identification number"),
        help_text=_(
            "Number sequence for identifying politically independent administrative units"
        ),
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        allow_unicode=True,
        verbose_name=_("URL parameter"),
        help_text=__(
            _("Unique string identifier without spaces and special characters."),
            _("Leave blank to generate unique parameter from name"),
        ),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.region_status`
    status = models.CharField(
        max_length=8,
        choices=region_status.CHOICES,
        default=region_status.HIDDEN,
        verbose_name=_("status"),
    )

    #: Manage choices in :mod:`~integreat_cms.cms.constants.administrative_division`.
    #: Also see `administrative division <https://en.wikipedia.org/wiki/Administrative_division>`__.
    administrative_division = models.CharField(
        max_length=24,
        choices=administrative_division.CHOICES,
        default=administrative_division.RURAL_DISTRICT,
        verbose_name=_("administrative division"),
    )
    aliases = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("aliases"),
        help_text=__(
            _("E.g. smaller municipalities in that area."),
            _("If empty, the CMS will try to fill this automatically."),
            _("Specify as JSON."),
        ),
    )
    custom_prefix = models.CharField(
        max_length=48,
        blank=True,
        verbose_name=_("custom prefix"),
        help_text=__(
            _("Enter parts of the name that should not affect sorting."),
            _(
                "Use this field only if the prefix is not an available choice in the list of administrative divisions above."
            ),
        ),
    )
    events_enabled = models.BooleanField(
        default=True,
        verbose_name=_("activate events"),
        help_text=_("Whether or not events are enabled in the region"),
    )
    locations_enabled = models.BooleanField(
        default=False,
        verbose_name=_("activate locations"),
        help_text=_("Whether or not locations are enabled in the region"),
    )
    push_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_("activate push notifications"),
        help_text=_("Whether or not push notifications are enabled in the region"),
    )
    latitude = models.FloatField(
        null=True,
        verbose_name=_("latitude"),
        help_text=_("The latitude coordinate of an approximate center of the region"),
    )
    longitude = models.FloatField(
        null=True,
        verbose_name=_("longitude"),
        help_text=_("The longitude coordinate of an approximate center of the region"),
    )
    longitude_min = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("minimum longitude"),
        help_text=_("The left boundary of the region"),
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )
    latitude_min = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("minimum latitude"),
        help_text=_("The bottom boundary of the region"),
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    longitude_max = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("maximum longitude"),
        help_text=_("The right boundary of the region"),
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )
    latitude_max = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("maximum latitude"),
        help_text=_("The top boundary of the region"),
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    postal_code = models.CharField(
        max_length=10,
        verbose_name=_("postal code"),
        help_text=_(
            "For districts, enter the postcode of the administrative headquarters."
        ),
    )

    admin_mail = models.EmailField(
        verbose_name=_("email address of the administrator"),
    )

    timezone = models.CharField(
        max_length=150,
        default=settings.CURRENT_TIME_ZONE,
        verbose_name=_("timezone"),
    )
    created_date = models.DateTimeField(
        default=django_timezone.now,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    statistics_enabled = models.BooleanField(
        default=False,
        verbose_name=_("activate statistics"),
        help_text=_("Whether or not statistics are enabled for the region"),
    )
    seo_enabled = models.BooleanField(
        default=False,
        verbose_name=_("activate SEO section"),
        help_text=_(
            "Enable possibility to fill meta description for pages, events and locations"
        ),
    )
    matomo_id = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Matomo ID"),
        help_text=__(
            _("The Matomo ID of this region."),
            _("Will be automatically derived from the Matomo access token."),
        ),
    )
    matomo_token = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name=_("Matomo authentication token"),
        help_text=_(
            "The secret Matomo access token of the region is used to authenticate in API requests"
        ),
    )

    page_permissions_enabled = models.BooleanField(
        default=False,
        verbose_name=_("activate page-specific permissions"),
        help_text=_(
            "This allows individual users to be granted the right to edit or publish a specific page."
        ),
    )

    icon = models.ForeignKey(
        "cms.MediaFile",
        verbose_name=_("logo"),
        on_delete=models.SET_NULL,
        related_name="icon_regions",
        blank=True,
        null=True,
    )

    chat_enabled = models.BooleanField(
        default=True,
        verbose_name=_("activate author chat"),
        help_text=_(
            "This gives all users of this region access to the cross-regional author chat."
        ),
    )

    administrative_division_included = models.BooleanField(
        default=False,
        verbose_name=_("include administrative division into name"),
        help_text=__(
            _(
                "Determines whether the administrative division is displayed next to the region name."
            ),
            _(
                "Sorting is always based on the name, independently from the administrative division."
            ),
        ),
    )

    offers = models.ManyToManyField(
        OfferTemplate,
        related_name="regions",
        blank=True,
        verbose_name=_("offers"),
        help_text=__(
            _(
                "Integreat offers are extended features apart from pages and events and are usually offered by a third party."
            ),
            _(
                "In most cases, the url is an external API endpoint which the frontend apps can query and render the results inside the Integreat app."
            ),
        ),
    )

    short_urls_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Activate short urls"),
        help_text=_("Please check the box if you want to use short urls."),
    )

    external_news_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Enable external news"),
        help_text=_(
            "Enable to display external articles in addition to local news managed by the CMS"
        ),
    )

    fallback_translations_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Show content in default language as fallback"),
        help_text=_(
            "Whether or not events and locations are shown in default language as fallback"
        ),
    )

    hix_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Activate HIX analysis"),
        help_text=_(
            "Allow users of this region to analyze understandability of text content via TextLab API."
        ),
    )

    summ_ai_enabled = models.BooleanField(
        default=False,
        verbose_name=_("activate automatic translations via SUMM.AI"),
        help_text=_(
            "Whether automatic translations into Easy German with SUMM.AI are enabled"
        ),
    )

    mt_renewal_month = models.PositiveIntegerField(
        choices=months.CHOICES,
        default=months.JANUARY,
        verbose_name=_("Credits renewal date for foreign language translation"),
        help_text=_("Budget usage will be reset on the 1st of the month"),
    )

    mt_addon_booked = models.BooleanField(
        default=False,
        verbose_name=_("Add-on package for foreign languages booked"),
        help_text=format_mt_help_text(
            _(
                "This makes {} translation credits available to the region in addition to the {} free ones."
            )
        ),
    )

    mt_midyear_start_month = models.PositiveIntegerField(
        default=None,
        blank=True,
        null=True,
        choices=months.CHOICES,
        verbose_name=_("Budget year start date for foreign language translation"),
        help_text=_("Month from which the add-on package was booked"),
    )

    mt_budget_used = models.PositiveIntegerField(
        default=0,
        verbose_name=_("used budget"),
    )

    machine_translate_pages = models.PositiveIntegerField(
        choices=machine_translation_permissions.CHOICES,
        default=machine_translation_permissions.EVERYONE,
        verbose_name=_("Pages"),
    )

    machine_translate_events = models.PositiveIntegerField(
        choices=machine_translation_permissions.CHOICES,
        default=machine_translation_permissions.EVERYONE,
        verbose_name=_("Events"),
    )

    machine_translate_pois = models.PositiveIntegerField(
        choices=machine_translation_permissions.CHOICES,
        default=machine_translation_permissions.EVERYONE,
        verbose_name=_("Locations"),
    )

    integreat_chat_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Enable Integreat Chat"),
        help_text=_("Toggle the Integreat Chat on/off."),
    )

    zammad_url = models.URLField(
        max_length=256,
        blank=True,
        default="",
        verbose_name=_("Zammad-URL"),
        help_text=_(
            "URL pointing to this region's Zammad instance. Setting this enables Zammad form offers."
        ),
    )
    zammad_access_token = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name=_("Zammad access token"),
        help_text=_(
            'Access token for a Zammad user account. In Zammad, the account must be part of the "Agent" role and have full group permissions for the group:'
        ),
    )
    zammad_chat_handlers = models.CharField(
        max_length=1024,
        blank=True,
        default="",
        verbose_name=_("Zammad chat handlers"),
        help_text=_(
            "Comma-separated email addresses of the accounts which should automatically be subscribed to new chat tickets. Note that these users must have full group permissions for the group:"
        ),
    )

    chat_beta_tester_percentage = models.IntegerField(
        default=0,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Chat beta tester percentage"),
        help_text=_(
            "Percentage of users selected as beta testers for the Integreat Chat feature"
        ),
    )

    #: Custom model manager :class:`~integreat_cms.cms.models.regions.region.RegionManager` for region objects
    objects = RegionManager()

    @cached_property
    def has_bounding_box(self) -> bool:
        """
        Whether the region has an individual bounding box

        :return: Whether all required coordinates for the bounding box are set
        """
        return all(
            [
                self.longitude_min,
                self.latitude_min,
                self.longitude_max,
                self.latitude_max,
            ]
        )

    @cached_property
    def bounding_box(self) -> BoundingBox:
        """
        The bounding box of the region

        :return: A bounding box object
        """
        if self.has_bounding_box:
            return BoundingBox(
                self.latitude_min,
                self.latitude_max,
                self.longitude_min,
                self.longitude_max,
            )
        return settings.DEFAULT_BOUNDING_BOX

    @cached_property
    def language_tree(self) -> list[LanguageTreeNode]:
        """
        This property returns a list of all
        :class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode` objects of this region.

        :return: A list of all language tree nodes of this region
        """
        # Prevent ValueError for unsaved regions
        if not self.pk:
            return []
        try:
            # Try to get the prefetched language tree
            return self.prefetched_language_tree_nodes
        except AttributeError:
            # If the tree was not prefetched, query it from the database
            # (this should only happen in rare edge cases)
            return list(self.language_tree_nodes.all().select_related("language"))

    @cached_property
    def language_node_by_id(self) -> dict[int, LanguageTreeNode]:
        """
        This property returns this region's language tree nodes indexed by ids

        :return: A mapping from language tree node ids to their language tree nodes in this region
        """
        return {node.id: node for node in self.language_tree}

    @cached_property
    def language_node_by_slug(self) -> dict[str, LanguageTreeNode]:
        """
        This property returns this region's language tree nodes indexed by slugs

        :return: A mapping from language slugs to their language tree nodes in this region
        """
        return {node.slug: node for node in self.language_tree}

    @cached_property
    def languages(self) -> list[Language]:
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects
        which have a :class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode` which belongs to
        this region.

        :return: A list of all :class:`~integreat_cms.cms.models.languages.language.Language` instances of this region
        """
        return [node.language for node in self.language_tree]

    def get_source_language(self, language_slug: str) -> Language | None:
        """
        This property returns this region's source language of a given language object

        :param language_slug: The slug of the requested language
        :return: The source language of the given language in this region
        """
        try:
            parent_id = self.language_node_by_slug.get(language_slug).parent_id
            return self.language_node_by_id.get(parent_id).language
        except AttributeError:
            return None

    @cached_property
    def active_languages(self) -> list[Language]:
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects
        which have  an active :class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode` which
        belongs to this region.

        :return: A list of all active :class:`~integreat_cms.cms.models.languages.language.Language` instances of this region
        """
        return [node.language for node in self.language_tree if node.active]

    @cached_property
    def visible_languages(self) -> list[Language]:
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects
        which have an active & visible :class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode`
        which belongs to this region.

        :return: A list of all active & visible :class:`~integreat_cms.cms.models.languages.language.Language` instances of this region
        """
        return [
            node.language for node in self.language_tree if node.active and node.visible
        ]

    @cached_property
    def language_tree_root(self) -> LanguageTreeNode | None:
        """
        This property returns a the root node of the region's language tree

        :return: The region's language root node
        """
        return next(iter(self.language_tree), None)

    @cached_property
    def default_language(self) -> Language | None:
        """
        This property returns the language :class:`~integreat_cms.cms.models.languages.language.Language` which
        corresponds to the root :class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode` of this
        region.

        :return: The root :class:`~integreat_cms.cms.models.languages.language.Language` of a region
        """
        return self.language_tree_root.language if self.language_tree_root else None

    @cached_property
    def prefix(self) -> str:
        """
        This property returns the administrative division of a region if it's included in the name.
        If this region has no default language, this property returns an empty string

        :return: The prefix of the region
        """
        if self.custom_prefix:
            return self.custom_prefix
        if self.administrative_division_included and self.default_language:
            # Get administrative division in region's default language
            with override(self.default_language.slug):
                return str(self.get_administrative_division_display())
        return ""

    @cached_property
    def full_name(self) -> str:
        """
        This property returns the full name of a region including its administrative division

        :return: The full name of the region
        """
        return f"{self.prefix} {self.name}".strip()

    @cached_property
    def region_users(self) -> QuerySet:
        """
        This property returns a QuerySet of all :class:`~django.contrib.auth.models.User` objects which belong to this
        region and are neither superusers nor staff.

        :return: A QuerySet of all :class:`~django.contrib.auth.models.User` object instances of a region
        """
        return get_user_model().objects.filter(
            regions=self,
            is_superuser=False,
            is_staff=False,
        )

    @cached_property
    def statistics(self) -> MatomoApiClient:
        """
        This property returns the MatomoApiClient of the current region.

        :return: The statistics manager
        """
        return MatomoApiClient(self)

    def get_language_or_404(
        self, language_slug: str, only_active: bool = False, only_visible: bool = False
    ) -> Language:
        """
        This class method returns the requested language of this region with optional filters ``active`` and ``visible``

        :param language_slug: The slug of the requested language
        :param only_active: Whether to return only active languages
        :param only_visible: Whether to return only visible languages
        :raises ~django.http.Http404: When no language with the given slug exists for this region and this filters

        :return: The requested :class:`~integreat_cms.cms.models.languages.language.Language` of this region
        """
        try:
            node = self.language_node_by_slug[language_slug]
            if only_active and not node.active:
                raise KeyError(
                    f"Language {node.language} is not active in region {self}"
                )
            if only_visible and not node.visible:
                raise KeyError(
                    f"Language {node.language} is not visible in region {self}"
                )
            return node.language
        except KeyError as e:
            raise Http404("No language matches the given query.") from e

    @property
    def explicitly_archived_ancestors_subquery(self) -> PageQuerySet:
        """
        This property returns a subquery for all explicitly archived ancestors of a given page.
        Needs to be used as part of another query because in order to resolve :class:`~django.db.models.OuterRef`,
        e.g. in a :class:`~django.db.models.Subquery` or in :class:`~django.db.models.Exists`.

        :return: A queryset of the explicitly archived ancestors.
        """

        return self.pages.filter(
            tree_id=models.OuterRef("tree_id"),
            lft__lt=models.OuterRef("lft"),
            rgt__gt=models.OuterRef("rgt"),
            explicitly_archived=True,
        )

    @cached_property
    def archived_pages(self) -> PageQuerySet:
        """
        This property returns a QuerySet of all archived pages and their descendants of this region.

        :return: A QuerySet of all archived pages of this region
        """

        return self.pages.filter(
            id=models.Case(
                models.When(
                    models.Exists(
                        self.explicitly_archived_ancestors_subquery.values("pk")
                    ),
                    then=models.F("pk"),
                ),
                models.When(
                    explicitly_archived=True,
                    then=models.F("pk"),
                ),
                default=None,
            )
        )

    @cached_property
    def non_archived_pages(self) -> PageQuerySet:
        """
        This property returns a QuerySet of all non-archived pages of this region.
        A page is considered as "non-archived" if its ``explicitly_archived`` property is ``False`` and all the
        page's ancestors are not archived as well.

        :return: A QuerySet of all non-archived pages of this region
        """

        return self.pages.filter(
            id=models.Case(
                models.When(
                    models.Exists(
                        self.explicitly_archived_ancestors_subquery.values("pk")
                    ),
                    then=None,
                ),
                default=models.F("pk"),
            ),
            explicitly_archived=False,
        )

    def get_pages(
        self,
        archived: bool = False,
        prefetch_translations: bool = False,
        prefetch_public_translations: bool = False,
        annotate_language_tree: bool = False,
    ) -> PageQuerySet:
        """
        This method returns either all archived or all non-archived pages of this region.
        To retrieve all pages independently of their archived-state, use the reverse foreign key
        :attr:`~integreat_cms.cms.models.regions.region.Region.pages`.

        :param archived: Whether or not only archived pages should be returned (default: ``False``)
        :param prefetch_translations: Whether the latest translations for each language should be prefetched (default: ``False``)
        :param prefetch_public_translations: Whether the latest public translations for each language should be prefetched (default: ``False``)
        :param annotate_language_tree: Whether the pages should be annotated with the region's language tree (default: ``False``)
        :return: Either the archived or the non-archived pages of this region
        """
        pages = self.archived_pages if archived else self.non_archived_pages
        if prefetch_translations:
            pages = pages.prefetch_translations()
        if prefetch_public_translations:
            pages = pages.prefetch_public_translations()
        if annotate_language_tree:
            pages = pages.annotate(language_tree=models.Subquery(self.language_tree))
        return pages

    def get_root_pages(self) -> PageQuerySet:
        """
        This method returns all root pages of this region.

        :return: This region's root pages
        """
        # Get model instead of importing it to avoid circular imports
        Page = apps.get_model(app_label="cms", model_name="Page")
        return Page.get_root_pages(region_slug=self.slug)

    @classmethod
    def search(cls, query: str) -> QuerySet[Region]:
        """
        Searches for all regions which match the given `query` in their name.
        :param query: The query string used for filtering the regions
        :return: A query for all matching objects
        """
        return cls.objects.filter(name__icontains=query)

    @cached_property
    def imprint(self) -> ImprintPage | None:
        """
        This property returns this region's imprint

        :return: The imprint of this region
        """
        return self.imprints.first()

    @property
    def mt_budget(self) -> int:
        """
        Calculate the maximum translation credit budget (number of words)

        :return: The region's total MT budget
        """
        # All regions which did not book the add-on get the free credits
        if not self.mt_addon_booked:
            return settings.MT_CREDITS_FREE
        # All regions which did book the add-on, but not mid-year, get the add-on credits
        if not self.mt_midyear_start_month:
            return settings.MT_CREDITS_ADDON + settings.MT_CREDITS_FREE
        # All regions which booked the add-on in mid-year get a fraction of the add-on credits
        # Calculate how many months lie between the renewal month and the start month of the add-on
        months_difference = self.mt_renewal_month - self.mt_midyear_start_month
        # Calculate the available fraction of the add-on
        multiplier = (months_difference % 12) / 12
        return int(multiplier * settings.MT_CREDITS_ADDON + settings.MT_CREDITS_FREE)

    @property
    def mt_budget_remaining(self) -> int:
        """
        Calculate the remaining translation credit budget (number of words)

        :return: The region's remaining MT budget
        """
        return max(0, self.mt_budget - self.mt_budget_used)

    @cached_property
    def backend_edit_link(self) -> str:
        """
        This function returns the absolute url to the edit form of this region

        :return: The url
        """
        return reverse(
            "edit_region",
            kwargs={
                "slug": self.slug,
            },
        )

    @cached_property
    def last_content_update(self) -> datetime:
        """
        Find the latest date at which any content of the
        region has been modified.

        :return: the last content update date
        """
        min_date = django_timezone.make_aware(
            django_timezone.datetime.min, django_timezone.get_default_timezone()
        )

        latest_page_update = (
            self.pages.aggregate(
                latest_update=models.Max("translations__last_updated")
            )["latest_update"]
            or min_date
        )
        latest_poi_update = (
            self.pois.aggregate(latest_update=models.Max("translations__last_updated"))[
                "latest_update"
            ]
            or min_date
        )
        latest_event_update = (
            self.events.aggregate(
                latest_update=models.Max("translations__last_updated")
            )["latest_update"]
            or min_date
        )
        latest_imprint_update = (
            self.imprint.translations.aggregate(
                latest_update=models.Max("last_updated")
            )["latest_update"]
            if self.imprint
            else None
        ) or min_date

        return max(
            latest_page_update,
            latest_poi_update,
            latest_event_update,
            latest_imprint_update,
            self.last_updated,
        )

    def __str__(self) -> SafeString:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Region object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the region
        """
        label = escape(self.full_name)
        if self.status == region_status.HIDDEN:
            # Add warning if region is hidden
            label += " (⚠ " + gettext("Hidden") + ")"
        elif self.status == region_status.ARCHIVED:
            # Add warning if region is archived
            label += " (⚠ " + gettext("Archived") + ")"
        # mark as safe so that the warning triangle is not escaped
        return mark_safe(label)

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Region: Region object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the region
        """
        return f"<Region (id: {self.id}, slug: {self.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("region")
        #: The plural verbose name of the model
        verbose_name_plural = _("regions")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The default sorting for this model
        ordering = ["name"]
