from __future__ import annotations

import json
import logging
from copy import deepcopy
from typing import TYPE_CHECKING
from zoneinfo import available_timezones

from celery import shared_task
from django import forms
from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override
from linkcheck.listeners import disable_listeners

from integreat_cms.core.management.commands.hix_bulk import calculate_hix_for_region

from ....gvz_api.utils import GvzRegion
from ....matomo_api.matomo_api_client import MatomoException
from ....nominatim_api.nominatim_api_client import NominatimApiClient
from ...constants import duplicate_pbo_behaviors, region_status, status
from ...models import LanguageTreeNode, OfferTemplate, Page, Region
from ...models.regions.region import format_summ_ai_help_text
from ...utils.slug_utils import generate_unique_slug_helper
from ...utils.translation_utils import gettext_many_lazy as __
from ..custom_model_form import CustomModelForm
from ..icon_widget import IconWidget

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.query import QuerySet

logger = logging.getLogger(__name__)


class CheckboxSelectMultipleWithDisabled(forms.CheckboxSelectMultiple):
    """
    This class adds functionality for disabling certain choices in the
    :class:`~django.forms.CheckboxSelectMultiple` widget
    """

    disabled_options: list[OfferTemplate] = []

    def create_option(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Overwrites the parent's method in order to disable
        a set of pre-determined options

        :return: a single option
        """
        option = super().create_option(*args, **kwargs)
        if option["value"].instance in self.disabled_options:
            option["attrs"]["class"] = "fake-disable fake-disable-region"
        return option


def get_timezone_choices() -> list[tuple[str, str]]:
    """
    This method generates the options for the second timezone dropdown

    :return: A list of all available timezones
    """
    timezones = list(available_timezones())
    timezones.sort()
    return [("", "---------")] + [
        (tz, tz.split("/", 1)[1].replace("_", " ")) for tz in timezones if "/" in tz
    ]


def get_timezone_area_choices() -> list[tuple[str, str]]:
    """
    This method generates the options for the first timezone dropdown.
    It displays the general area of a country or city. Often the continent.

    :return: A list of the general areas of the timezones
    """
    timezone_regions = list(
        {
            tz.split("/")[0]
            for tz in available_timezones()
            if "/" in tz and "Etc" not in tz and "SystemV" not in tz
        },
    )
    timezone_regions.sort()
    return (
        [("", "---------")]
        + [(tzr, tzr) for tzr in timezone_regions]
        + [("Etc", _("Other timezones"))]
    )


class RegionForm(CustomModelForm):
    """
    Form for creating and modifying region objects
    """

    duplicated_region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        label=_("Copy languages, pages and media from another region"),
        empty_label=_("Do no import initial content"),
        required=False,
    )

    duplication_keep_status = forms.BooleanField(
        required=False,
        label=_("Keep publication status of pages"),
        help_text=_(
            "Enable it to keep the initial publication status of the pages and don't overwrite them to draft.",
        ),
    )

    duplication_keep_translations = forms.BooleanField(
        required=False,
        label=_("Copy languages and content translations"),
        help_text=_(
            "Disable to skip copying of the language tree and all content translations.",
        ),
        initial=True,
    )

    duplication_pbo_behavior = forms.ChoiceField(
        choices=duplicate_pbo_behaviors.CHOICES,
        initial=duplicate_pbo_behaviors.ACTIVATE,
        widget=forms.Select,
        required=False,
        label=_("Page based offers cloning behavior"),
        help_text=_(
            "Decide whether offers which have not been activated but are required for embedded content should be auto-activated, or their embeddings be ignored during cloning.",
        ),
    )

    timezone_area = forms.ChoiceField(
        choices=get_timezone_area_choices,
        label=_("Timezone area"),
        required=False,
    )

    summ_ai_midyear_start_enabled = forms.BooleanField(
        required=False,
        label=_("Budget year start differs from the renewal date"),
        help_text=__(
            _("Enable to set starting date differing from the renewal date."),
            format_summ_ai_help_text(
                _("Budget will be set as a monthly fraction of {} credits")
            ),
        ),
    )

    mt_midyear_start_enabled = forms.BooleanField(
        required=False,
        label=_("Budget year start differs from the renewal date"),
        help_text=_(
            "Enable to set an starting date of machine translation budget calculation differing from the renewal date. Budget will be set as a monthly fraction of the booked machine translation budget.",
        ),
    )

    zammad_offers = forms.ModelMultipleChoiceField(
        queryset=OfferTemplate.objects.filter(is_zammad_form=True),
        required=False,
        label=_("Zammad forms"),
        help_text=_(
            "Zammad forms are a type of offer which can only be used if a Zammad-URL is provided for the region.",
        ),
        widget=CheckboxSelectMultipleWithDisabled(),
    )

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Region
        #: The fields of the model which should be handled by this form
        fields = [
            "name",
            "common_id",
            "slug",
            "events_enabled",
            "locations_enabled",
            "chat_enabled",
            "push_notifications_enabled",
            "latitude",
            "longitude",
            "longitude_min",
            "latitude_min",
            "longitude_max",
            "latitude_max",
            "postal_code",
            "admin_mail",
            "statistics_enabled",
            "matomo_id",
            "matomo_token",
            "status",
            "page_permissions_enabled",
            "administrative_division",
            "aliases",
            "icon",
            "administrative_division_included",
            "offers",
            "short_urls_enabled",
            "seo_enabled",
            "custom_prefix",
            "external_news_enabled",
            "timezone",
            "fallback_translations_enabled",
            "summ_ai_enabled",
            "summ_ai_renewal_month",
            "summ_ai_midyear_start_enabled",
            "summ_ai_midyear_start_month",
            "hix_enabled",
            "mt_budget_booked",
            "mt_renewal_month",
            "mt_midyear_start_enabled",
            "mt_midyear_start_month",
            "integreat_chat_enabled",
            "zammad_url",
            "zammad_access_token",
            "zammad_webhook_token",
            "zammad_privacy_policy",
            "chat_beta_tester_percentage",
        ]
        #: The widgets which are used in this form
        widgets = {
            "timezone": forms.Select(choices=get_timezone_choices()),
            "icon": IconWidget(),
            "offers": CheckboxSelectMultipleWithDisabled(),
            "zammad_access_token": forms.PasswordInput(),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        r"""
        Initialize region form

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        """
        super().__init__(*args, **kwargs)
        if "/" in self.instance.timezone:
            self.fields["timezone_area"].initial = self.instance.timezone.split("/")[0]
        self.fields["slug"].required = False
        # Do not require coordinates because they might be automatically filled
        self.fields["latitude"].required = False
        self.fields["longitude"].required = False
        # Disable SUMM.AI option if locally and globally disabled
        if not settings.SUMM_AI_ENABLED and not self.instance.summ_ai_enabled:
            self.fields["summ_ai_enabled"].disabled = True
        if not settings.TEXTLAB_API_ENABLED and not self.instance.hix_enabled:
            self.fields["hix_enabled"].disabled = True
        self.fields["summ_ai_midyear_start_enabled"].initial = (
            self.instance.summ_ai_midyear_start_month is not None
        )
        self.fields["mt_midyear_start_enabled"].initial = (
            self.instance.mt_midyear_start_month is not None
        )
        self.disabled_offer_options = (
            OfferTemplate.objects.filter(pages__region=self.instance)
            if self.instance.id
            else OfferTemplate.objects.none()
        )
        self.fields["offers"].queryset = OfferTemplate.objects.filter(
            is_zammad_form=False,
        )
        self.fields["offers"].widget.disabled_options = self.disabled_offer_options

        self.fields[
            "zammad_offers"
        ].widget.disabled_options = self.disabled_offer_options
        self.fields["zammad_offers"].initial = (
            self.instance.offers.filter(is_zammad_form=True) if self.instance.id else []
        )

    def save(self, commit: bool = True) -> Region:
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :return: The saved region object
        """

        # Only duplicate content if region is created and a region was selected
        duplicate_region = (
            not self.instance.id and self.cleaned_data["duplicated_region"]
        )

        if duplicate_region:
            self.instance.status = region_status.IN_CLONING
            self.instance.hix_enabled = False

        # Save CustomModelForm
        region = super().save(commit=commit)

        if duplicate_region:
            # Disable HIX during the duplication process,
            # to skip recalculation for already known content
            source_region = self.cleaned_data["duplicated_region"]
            keep_status = self.cleaned_data["duplication_keep_status"]
            keep_translations = self.cleaned_data["duplication_keep_translations"]

            # Determine offers to force activate or to skip when cloning pages
            required_offers = OfferTemplate.objects.filter(pages__region=source_region)
            if (
                self.cleaned_data["duplication_pbo_behavior"]
                == duplicate_pbo_behaviors.ACTIVATE
            ):
                region.offers.set(region.offers.union(required_offers))
                # Even is ACTIVATE behavior was selected, Zammad forms need to be skipped during cloning if no Zammad URL is set
                offers_to_discard = (
                    None
                    if region.zammad_url
                    else OfferTemplate.objects.filter(is_zammad_form=True)
                )
            else:
                offers_to_discard = required_offers.exclude(
                    id__in=region.offers.values_list("id", flat=True),
                )

            async_clone_region_content.apply_async(
                args=[
                    source_region.pk,
                    region.pk,
                    keep_status,
                    keep_translations,
                    self.cleaned_data["hix_enabled"],
                    self.cleaned_data["status"],
                    [offer.pk for offer in offers_to_discard]
                    if offers_to_discard
                    else None,
                ]
            )
        return region

    def clean(self) -> dict[str, Any]:
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        """
        cleaned_data = super().clean()

        cleaned_data.update(self.clean_statistics())
        cleaned_data.update(self.clean_summ_ai())
        cleaned_data.update(self.clean_mt_budget())
        cleaned_data.update(self.clean_zammad())
        cleaned_data.update(self.clean_chat())
        cleaned_data.update(self.clean_gvz())
        cleaned_data.update(self.clean_coordinates())
        cleaned_data.update(self.clean_duplicate_region())
        self.autofill_bounding_box(cleaned_data)

        logger.debug("RegionForm validated [2] with cleaned data %r", cleaned_data)
        return cleaned_data

    def clean_statistics(self) -> dict[str, Any]:
        """
        Check whether statistics can be enabled
        This is not a typical django method cleaning only one, but a group of fields, and has to be called explicitly.
        """
        relevant_fields = [
            "statistics_enabled",
            "matomo_token",
            "matomo_id",
        ]
        cleaned: dict[str, Any] = {
            key: self.cleaned_data[key]
            for key in relevant_fields
            if key in self.cleaned_data
        }

        if cleaned["statistics_enabled"] and not cleaned["matomo_token"]:
            self.add_error(
                "statistics_enabled",
                _(
                    "Statistics can only be enabled when a valid access token is supplied.",
                ),
            )
        # Automatically set the Matomo ID
        if cleaned["matomo_token"]:
            try:
                cleaned["matomo_id"] = self.instance.statistics.get_matomo_id(
                    token_auth=cleaned["matomo_token"],
                )
            except MatomoException:
                logger.exception("")
                self.add_error(
                    "matomo_token",
                    _("The provided access token is invalid."),
                )
        else:
            cleaned["matomo_id"] = None

        return cleaned

    def clean_mt_budget(self) -> dict[str, Any]:
        """
        If MT budget year differs from the set renewal date, make sure a budget year start date is set
        This is not a typical django method cleaning only one, but a group of fields, and has to be called explicitly.
        """
        relevant_fields = [
            "mt_midyear_start_enabled",
            "mt_midyear_start_month",
            "mt_renewal_month",
        ]
        cleaned: dict[str, Any] = {
            key: self.cleaned_data[key]
            for key in relevant_fields
            if key in self.cleaned_data
        }

        if (
            cleaned["mt_midyear_start_enabled"]
            and cleaned["mt_midyear_start_month"] is None
        ):
            self.add_error(
                "mt_midyear_start_month",
                _(
                    "Please provide a valid budget year start date for foreign language translation.",
                ),
            )
        elif (
            not cleaned["mt_midyear_start_enabled"]
            or cleaned["mt_midyear_start_month"] == cleaned["mt_renewal_month"]
        ):
            cleaned["mt_midyear_start_month"] = None
        return cleaned

    def clean_summ_ai(self) -> dict[str, Any]:
        """
        If Summ AI budget year differs from the set renewal date, make sure a budget year start date is set.
        This is not a typical django method cleaning only one, but a group of fields, and has to be called explicitly.
        """
        relevant_fields = [
            "summ_ai_midyear_start_enabled",
            "summ_ai_midyear_start_month",
            "summ_ai_renewal_month",
        ]
        cleaned: dict[str, Any] = {
            key: self.cleaned_data[key]
            for key in relevant_fields
            if key in self.cleaned_data
        }

        if (
            cleaned["summ_ai_midyear_start_enabled"]
            and cleaned["summ_ai_midyear_start_month"] is None
        ):
            self.add_error(
                "summ_ai_midyear_start_month",
                _(
                    "Please provide a valid budget year start date for simplified language translation."
                ),
            )
        elif (
            not cleaned["summ_ai_midyear_start_enabled"]
            or cleaned["summ_ai_midyear_start_month"]
            == cleaned["summ_ai_renewal_month"]
        ):
            cleaned["summ_ai_midyear_start_month"] = None
        return cleaned

    def clean_zammad(self) -> dict[str, Any]:
        """
        Re-combine all offers and make sure no non-disableable offers have been disabled
        This is not a typical django method cleaning only one, but a group of fields, and has to be called explicitly.
        """
        relevant_fields = [
            "zammad_url",
            "zammad_offers",
            "zammad_webhook_token",
            "offers",
        ]
        cleaned: dict[str, Any] = {
            key: self.cleaned_data[key]
            for key in relevant_fields
            if key in self.cleaned_data
        }

        if not cleaned["zammad_url"]:
            cleaned["zammad_offers"] = []
        cleaned["offers"] = list(cleaned["offers"]) + list(
            cleaned["zammad_offers"],
        )
        if self.disabled_offer_options and not all(
            offer in cleaned["offers"] for offer in self.disabled_offer_options
        ):
            self.add_error(
                "offers",
                _(
                    "Some offers could not be disabled, since they are currently embedded in at least one page.",
                ),
            )
        return cleaned

    def clean_chat(self) -> dict[str, Any]:
        """
        Public chat can only be enabled if Zammad URL and access key are set
        This is not a typical django method cleaning only one, but a group of fields, and has to be called explicitly.
        """
        relevant_fields = [
            "integreat_chat_enabled",
        ]
        cleaned: dict[str, Any] = {
            key: self.cleaned_data[key]
            for key in relevant_fields
            if key in self.cleaned_data
        }

        if cleaned["integreat_chat_enabled"] and (
            not cleaned["zammad_url"]
            or not cleaned["zammad_access_token"]
            or not cleaned["zammad_webhook_token"]
        ):
            self.add_error(
                "integreat_chat_enabled",
                _(
                    "A Zammad URL, Zammad Webhook Token and Access Token are required in order to enable the public chat.",
                ),
            )
        return cleaned

    def clean_gvz(self) -> dict[str, Any]:
        """
        Get additional data from GVZ API
        This is not a typical django method cleaning only one, but a group of fields, and has to be called explicitly.
        """
        relevant_fields = [
            "name",
            "common_id",
            "administrative_division",
            "aliases",
        ]
        cleaned: dict[str, Any] = {
            key: self.cleaned_data[key]
            for key in relevant_fields
            if key in self.cleaned_data
        }

        if apps.get_app_config("gvz_api").api_available:
            gvz_region = GvzRegion(
                region_name=cleaned["name"],
                region_ags=cleaned["common_id"],
                region_type=cleaned["administrative_division"],
            )
            logger.debug("GVZ API match: %r", gvz_region)
            if gvz_region.child_coordinates and not cleaned.get("aliases"):
                cleaned["aliases"] = gvz_region.child_coordinates
            if gvz_region.longitude and not self.cleaned_data.get("longitude"):
                cleaned["longitude"] = gvz_region.longitude
            if gvz_region.latitude and not self.cleaned_data.get("latitude"):
                cleaned["latitude"] = gvz_region.latitude
            if gvz_region.ags and not cleaned.get("common_id"):
                cleaned["common_id"] = gvz_region.ags
        return cleaned

    def clean_coordinates(self) -> dict[str, Any]:
        """
        If the coordinates could not be filled automatically and have not been filled manually either, throw an error
        This is not a typical django method cleaning only one, but a group of fields, and has to be called explicitly.
        """
        relevant_fields = [
            "longitude",
            "latitude",
        ]
        cleaned: dict[str, Any] = {
            key: self.cleaned_data[key]
            for key in relevant_fields
            if key in self.cleaned_data
        }

        if not cleaned.get("latitude"):
            self.add_error(
                "latitude",
                forms.ValidationError(
                    _(
                        "Could not retrieve the coordinates automatically, please fill the field manually.",
                    ),
                    code="required",
                ),
            )
        if not cleaned.get("longitude"):
            self.add_error(
                "longitude",
                forms.ValidationError(
                    _(
                        "Could not retrieve the coordinates automatically, please fill the field manually.",
                    ),
                    code="required",
                ),
            )
        return cleaned

    def clean_duplicate_region(self) -> dict[str, Any]:
        """
        If a region is being cloned but no PBO cloning behavior has been selected, throw an error
        This is not a typical django method cleaning only one, but a group of fields, and has to be called explicitly.
        """
        relevant_fields = [
            "duplicated_region",
            "duplication_pbo_behavior",
        ]
        cleaned: dict[str, Any] = {
            key: self.cleaned_data[key]
            for key in relevant_fields
            if key in self.cleaned_data
        }

        if cleaned.get("duplicated_region") and not cleaned.get(
            "duplication_pbo_behavior",
        ):
            self.add_error(
                "duplication_pbo_behavior",
                forms.ValidationError(
                    _("Please choose a behavior for cloning embedded offers."),
                    code="required",
                ),
            )
        return cleaned

    def clean_slug(self) -> str:
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        """
        return generate_unique_slug_helper(self, "region")

    def clean_custom_prefix(self) -> str:
        """
        Validate the custom prefix field. (see :ref:`overriding-modelform-clean-method`)

        :return: The given prefix or ``None`` if it is invalid
        """
        cleaned_data = self.cleaned_data
        # Validate custom prefix
        if cleaned_data.get("custom_prefix"):
            # Get the administrative divisions as conflicting options
            administrative_divisions = [
                label
                for choice, label in self.fields["administrative_division"].choices
            ]
            for language_slug, language_name in settings.LANGUAGES:
                # Check if at least one translation of the labels matches the prefix
                with override(language_slug):
                    # Force evaluation of lazy-translated text
                    translated_administrative_divisions = list(
                        map(str, administrative_divisions),
                    )
                # Check if custom prefix could also be set via the administrative division
                if (
                    cleaned_data.get("custom_prefix")
                    in translated_administrative_divisions
                ):
                    error_messages = []
                    # Get currently selected administrative division
                    selected_administrative_division = dict(
                        self.fields["administrative_division"].choices,
                    )[cleaned_data.get("administrative_division")]
                    # Check if administrative division needs to be changed to translated version
                    if cleaned_data.get("custom_prefix") in administrative_divisions:
                        desired_administrative_division = cleaned_data.get(
                            "custom_prefix",
                        )
                    else:
                        # Get index of translated administrative division
                        index = translated_administrative_divisions.index(
                            cleaned_data.get("custom_prefix"),
                        )
                        # Get original label which needs to be selected in list
                        desired_administrative_division = administrative_divisions[
                            index
                        ]
                    if (
                        selected_administrative_division
                        == desired_administrative_division
                    ):
                        error_messages.append(
                            _(
                                "'{}' is already selected as administrative division.",
                            ).format(selected_administrative_division),
                        )
                    else:
                        error_messages.append(
                            _("Please select '{}' as administrative division.").format(
                                desired_administrative_division,
                            ),
                        )
                    # Check if default language needs to be changed in order to use this administrative division
                    if (
                        not self.instance.default_language
                        or self.instance.default_language.native_name != language_name
                    ):
                        error_messages.append(
                            _(
                                "Please set {} as default language for this region.",
                            ).format(_(language_name)),
                        )
                    # Check if administrative division is included in name yet
                    if not cleaned_data.get("administrative_division_included"):
                        error_messages.append(
                            _("Please enable '{}'.").format(
                                self.fields["administrative_division_included"].label,
                            ),
                        )
                    self.add_error(
                        "custom_prefix",
                        __(*error_messages),
                    )
        # Check if administrative division is also included in the name and allow only one of both prefix options
        if cleaned_data.get("custom_prefix") and cleaned_data.get(
            "administrative_division_included",
        ):
            self.add_error(
                "custom_prefix",
                _(
                    "You cannot include the administrative division into the name and use a custom prefix at the same time.",
                ),
            )
        return cleaned_data.get("custom_prefix")

    def clean_aliases(self) -> dict:
        """
        Validate the aliases field (see :ref:`overriding-modelform-clean-method`).

        :return: The valid aliases
        """
        cleaned_aliases = self.cleaned_data["aliases"]
        # If a string is given, try to load as JSON string
        if isinstance(cleaned_aliases, str):
            try:
                cleaned_aliases = json.loads(cleaned_aliases)
            except json.JSONDecodeError:
                self.add_error("aliases", _("Enter a valid JSON."))
        # Convert None to an empty dict
        return cleaned_aliases or {}

    def clean_summ_ai_enabled(self) -> bool:
        """
        Validate the summ_ai_enabled field (see :ref:`overriding-modelform-clean-method`)

        :return: The validated field whether SUMM.AI is enabled
        """
        if self.cleaned_data.get("summ_ai_enabled") and not settings.SUMM_AI_ENABLED:
            self.add_error(
                "summ_ai_enabled",
                _("Currently SUMM.AI is globally deactivated"),
            )
            return False
        return self.cleaned_data.get("summ_ai_enabled")

    def clean_hix_enabled(self) -> bool:
        """
        Validate the hix_enabled field (see :ref:`overriding-modelform-clean-method`).

        :return: The validated field
        """
        cleaned_hix_enabled = self.cleaned_data["hix_enabled"]
        # Check whether someone tries to activate hix when no API key is set
        if cleaned_hix_enabled and not settings.TEXTLAB_API_ENABLED:
            self.add_error(
                "hix_enabled",
                _("No Textlab API key is set on this system."),
            )
        return cleaned_hix_enabled

    def clean_zammad_url(self) -> str:
        """
        Validate the zammad_url field (see :ref:`overriding-modelform-clean-method`).

        :return: The validated field
        """
        if not (cleaned_zammad_url := self.cleaned_data["zammad_url"]):
            return ""
        # Remove superfluous path parts
        cleaned_zammad_url = cleaned_zammad_url.split("/api/v1")[0]
        return cleaned_zammad_url.rstrip("/")

    def clean_zammad_access_token(self) -> str:
        """
        Validate the zammad_access_token field (see :ref:`overriding-modelform-clean-method`).
        If the value is empty, keep the original one.

        :return: The validated field
        """
        return (
            self.cleaned_data["zammad_access_token"]
            if self.cleaned_data["zammad_access_token"]
            else self.instance.zammad_access_token
        )

    @staticmethod
    def autofill_bounding_box(cleaned_data: dict[str, Any]) -> dict[str, Any]:
        """
        Automatically fill the bounding box coordinates

        :param cleaned_data: The partially cleaned data
        :return: The updated cleaned data
        """
        # When the Nominatim API is enabled, auto fill the bounding box coordinates
        if settings.NOMINATIM_API_ENABLED:
            nominatim_api_client = NominatimApiClient()
            if bounding_box := nominatim_api_client.get_bounding_box(
                administrative_division=cleaned_data.get("administrative_division", ""),
                name=cleaned_data.get("name", ""),
                aliases=cleaned_data.get("aliases", ""),
            ):
                # Update bounding box values if not set manually
                if not cleaned_data.get("latitude_min"):
                    cleaned_data["latitude_min"] = bounding_box.latitude_min
                if not cleaned_data.get("latitude_max"):
                    cleaned_data["latitude_max"] = bounding_box.latitude_max
                if not cleaned_data.get("longitude_min"):
                    cleaned_data["longitude_min"] = bounding_box.longitude_min
                if not cleaned_data.get("longitude_max"):
                    cleaned_data["longitude_max"] = bounding_box.longitude_max

        return cleaned_data


@shared_task
def async_clone_region_content(
    source_region_id: int,
    target_region_id: int,
    keep_status: bool,
    keep_translations: bool,
    hix_enabled: bool,
    target_region_status: str,
    offers_to_discard_ids: list[int] | None,
) -> None:
    source_region = Region.objects.get(id=source_region_id)
    region = Region.objects.get(id=target_region_id)
    try:
        offers_to_discard = (
            OfferTemplate.objects.filter(id__in=offers_to_discard_ids)
            if offers_to_discard_ids
            else None
        )

        # Duplicate language tree
        logger.info("Duplicating language tree of %r to %r", source_region, region)
        duplicate_language_tree(
            source_region,
            region,
            only_root=not keep_translations,
        )
        # Disable linkcheck listeners to prevent links to be created for outdated versions
        with disable_listeners():
            # Duplicate pages
            logger.info("Duplicating page tree of %r to %r", source_region, region)
            duplicate_pages(
                source_region,
                region,
                keep_status=keep_status,
                offers_to_discard=offers_to_discard,
                only_root=not keep_translations,
            )
            # Duplicate Imprint
            if source_region.imprint:
                logger.info(
                    "Duplicating imprint of %r to %r",
                    source_region,
                    region,
                )
                duplicate_imprint(source_region, region)
        # Duplicate media content
        duplicate_media(source_region, region)

        adjust_hix_setting_and_region_status(region, hix_enabled, target_region_status)
    except Exception:
        logger.exception("Error during region cloning")
        region.status = region_status.CLONING_ERROR
        region.save()


def duplicate_language_tree(
    source_region: Region,
    target_region: Region,
    source_parent: LanguageTreeNode | None = None,
    target_parent: LanguageTreeNode | None = None,
    logging_prefix: str = "",
    only_root: bool = False,
) -> None:
    """
    Function to duplicate the language tree of one region to another.

    Usage: duplicate_language_tree(source_region, target_region)

    This is a recursive function to walk the whole language tree. It starts at root level with the default parent None.
    The recursion is necessary because the new nodes need their correct (also duplicated) parent node.

    :param source_region: The region from which the language tree should be duplicated
    :param target_region: The region to which the language tree should be added
    :param source_parent: The current parent node id of the recursion
    :param target_parent: The node of the target region which is the duplicate of the source parent node
    :param logging_prefix: recursion level to get a pretty log output
    :param only_root: Set if only the root node should be copied, not its children
    """
    logger.debug(
        "%s Duplicating child nodes",
        logging_prefix + "└─",
    )
    logging_prefix += "  "

    # Iterate over all children of the current source parent, beginning with the root node
    source_nodes = source_region.language_tree_nodes.filter(parent=source_parent)
    num_source_nodes = len(source_nodes)
    for i, source_node in enumerate(source_nodes):
        logger.debug(
            "%s Duplicating node %r",
            logging_prefix + ("└─" if i == num_source_nodes - 1 else "├─"),
            source_node,
        )
        row_logging_prefix = logging_prefix + (
            "  " if i == num_source_nodes - 1 else "│  "
        )
        if target_parent:
            # If the target parent already exists, we inherit its tree id for all its sub nodes
            target_tree_id = target_parent.tree_id
        else:
            # If the language tree node is a root node, we need to assign a new tree id
            last_root_node = LanguageTreeNode.get_last_root_node()
            target_tree_id = last_root_node.tree_id + 1
            logger.debug(
                "%s Node is a root node, assigning new tree_id %r",
                row_logging_prefix + "├─",
                target_tree_id,
            )
        # Copy the target node to leave the source node unchanged for next iteration
        target_node = deepcopy(source_node)
        # Change the region and parent to its new values
        target_node.region = target_region
        target_node.parent = target_parent
        # Set new tree id
        target_node.tree_id = target_tree_id
        # Delete the primary key to force an insert
        target_node.pk = None
        # Fix lft and rgt of the tree if the children of this node should not be cloned
        # Otherwise, the tree structure will be inconsistent
        if only_root:
            target_node.lft = 1
            target_node.rgt = 2
        # Check if the resulting node is valid
        target_node.full_clean()
        # Save the duplicated node
        target_node.save()
        logger.debug(
            "%s Created target node %r",
            row_logging_prefix + ("└─" if source_node.is_leaf() else "├─"),
            target_node,
        )
        if not (source_node.is_leaf() or only_root):
            # Call the function recursively for all children of the current node
            duplicate_language_tree(
                source_region,
                target_region,
                source_node,
                target_node,
                row_logging_prefix,
            )


def duplicate_pages(
    source_region: Region,
    target_region: Region,
    source_parent: Page | None = None,
    target_parent: Page | None = None,
    logging_prefix: str = "",
    keep_status: bool = False,
    offers_to_discard: QuerySet[OfferTemplate] | None = None,
    only_root: bool = False,
) -> None:
    """
    Function to duplicate all non-archived pages from one region to another

    Usage: duplicate_pages(source_region, target_region)

    This is a recursive function to walk the whole page tree. It starts at root level with the default parent None.
    The recursion is necessary because the new pages need their correct (also duplicated) parent page.

    :param source_region: The region from which the pages should be duplicated
    :param target_region: The region to which the pages should be added
    :param source_parent: The current parent page id of the recursion
    :param target_parent: The page of the target region which is the duplicate of the source parent page
    :param logging_prefix: Recursion level to get a pretty log output
    :param keep_status: Parameter to indicate whether the status of the cloned pages should be kept
    :param offers_to_discard: Offers which might be embedded in the source region, but not in the target region
    :param only_root: Set if only the root node should be copied, not its children
    """

    logger.debug(
        "%s Duplicating child nodes",
        logging_prefix + "└─",
    )
    logging_prefix += "  "

    # At first, get all pages from the source region with a specific parent page, except archived ones
    # As the parent will be None for the initial call, this returns all pages from the root level
    source_pages = source_region.pages.filter(
        parent=source_parent,
        explicitly_archived=False,
    )
    num_source_pages = len(source_pages)
    for i, source_page in enumerate(source_pages):
        logger.debug(
            "%s Duplicating page %r",
            logging_prefix + ("└─" if i == num_source_pages - 1 else "├─"),
            source_page,
        )
        row_logging_prefix = logging_prefix + (
            "  " if i == num_source_pages - 1 else "│  "
        )
        if target_parent:
            # If the target parent already exist, we inherit its tree id for all its subpages
            target_tree_id = target_parent.tree_id
        else:
            # If the page is a root page, we need to assign a new tree id
            last_root_page = Page.get_last_root_node()
            target_tree_id = last_root_page.tree_id + 1
            logger.debug(
                "%s Page is a root page, assigning new tree_id %r",
                row_logging_prefix + "├─",
                target_tree_id,
            )
        # Copy the target node to leave the source node unchanged for next iteration
        target_page = deepcopy(source_page)
        # Set the parent of the new page to the previously created target parent
        target_page.parent = target_parent
        # Set the region of the new page to the target region
        target_page.region = target_region
        # Set new tree id
        target_page.tree_id = target_tree_id
        # Delete the primary key to duplicate the object instance instead of updating it
        target_page.pk = None
        # Set push API token to blank for duplicated page
        target_page.api_token = ""
        # Check if the page is valid
        target_page.full_clean()
        # Save duplicated page
        target_page.save()
        # Set embedded offers ManyToMany field
        embedded_offers = (
            source_page.embedded_offers.all()
            if not offers_to_discard
            else source_page.embedded_offers.exclude(
                id__in=offers_to_discard.values_list("id", flat=True),
            )
        )
        target_page.embedded_offers.add(*embedded_offers)
        logger.debug(
            "%s Created %r",
            row_logging_prefix + "├─",
            target_page,
        )
        duplicate_page_translations(
            source_page,
            target_page,
            row_logging_prefix,
            keep_status,
        )
        if not source_page.is_leaf():
            # Recursively call this function with the current pages as new parents
            duplicate_pages(
                source_region,
                target_region,
                source_page,
                target_page,
                row_logging_prefix,
                keep_status,
                offers_to_discard,
                only_root,
            )


def duplicate_page_translations(
    source_page: Page,
    target_page: Page,
    logging_prefix: str,
    keep_status: bool,
) -> None:
    """
    Duplicate all translations of a given source page to a given target page

    :param source_page: The given source page
    :param target_page: The desired target page
    :param logging_prefix: The prefix to be used for logging
    :param keep_status: Parameter to indicate whether the status of the cloned pages should be kept
    """
    logger.debug(
        "%s Duplicating page translations",
        logging_prefix + ("└─" if source_page.is_leaf() else "├─"),
    )
    # Clone all page translations of the source page
    source_page_translations = source_page.translations.filter(
        language__in=[
            node.language for node in target_page.region.language_tree_nodes.all()
        ],
    )
    num_translations = len(source_page_translations)
    translation_row_logging_prefix = logging_prefix + (
        "  " if source_page.is_leaf() else "│  "
    )

    for i, page_translation in enumerate(source_page_translations):
        # Set the page of the source translation to the new page
        page_translation.page = target_page
        # Delete the primary key to duplicate the object instance instead of updating it
        page_translation.pk = None
        # Set the translation to draft if keep_status is false
        if keep_status is False:
            page_translation.status = status.DRAFT
        # Check if the page translation is valid
        page_translation.full_clean()
        # Save duplicated page translation
        page_translation.save(update_timestamp=False)
        logger.debug(
            "%s Created %r",
            translation_row_logging_prefix
            + ("└─" if i == num_translations - 1 else "├─"),
            page_translation,
        )


def duplicate_imprint(
    source_region: Region,
    target_region: Region,
    only_root: bool = False,
) -> None:
    """
    Function to duplicate the imprint from one region to another.

    :param source_region: the source region from which the imprint should be duplicated
    :param target_region: the target region
    :param only_root: Set if only the root node should be copied, not its children
    """
    source_imprint = source_region.imprint
    target_imprint = deepcopy(source_imprint)
    target_imprint.region = target_region
    # Delete the primary key to duplicate the object instance instead of updating it
    target_imprint.pk = None
    # Check if the new imprint object is valid
    target_imprint.full_clean()

    target_imprint.save()

    if only_root:
        return

    # Duplicate imprint translations by iterating to all existing ones
    source_page_translations = source_imprint.translations.all()

    for imprint_translation in source_page_translations:
        # Set the page of the source translation to the new imprint
        imprint_translation.page = target_imprint
        # Delete the primary key to duplicate the object instance instead of updating it
        imprint_translation.pk = None
        # Set the translation to draft
        imprint_translation.status = status.DRAFT
        # Check if the imprint translation is valid
        imprint_translation.full_clean()
        # Save duplicated imprint translation
        imprint_translation.save(update_timestamp=False)


def duplicate_media(
    _source_region: Region,
    _target_region: Region,
) -> None:
    """
    Function to duplicate all media of one region to another.
    """
    # TODO(timobrembeck): implement duplication of all media files
    # https://github.com/digitalfabrik/integreat-cms/issues/1414


def adjust_hix_setting_and_region_status(
    region: Region,
    hix_enabled: bool,
    target_region_status: str,
) -> None:
    region.hix_enabled = hix_enabled
    region.status = target_region_status
    region.save()

    if settings.TEXTLAB_API_ENABLED and hix_enabled:
        with disable_listeners():
            calculate_hix_for_region(region)
