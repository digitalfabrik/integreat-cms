import json
import logging

from copy import deepcopy

from zoneinfo import available_timezones
from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import override, gettext_lazy as _
from django.apps import apps

from linkcheck.listeners import disable_listeners
from linkcheck.models import Link

from ....nominatim_api.nominatim_api_client import NominatimApiClient
from ....gvz_api.utils import GvzRegion
from ...constants import status
from ...models import Region, Page, PageTranslation, LanguageTreeNode
from ....matomo_api.matomo_api_client import MatomoException
from ...models.regions.region import format_deepl_help_text
from ...utils.slug_utils import generate_unique_slug_helper
from ...utils.translation_utils import gettext_many_lazy as __
from ..icon_widget import IconWidget
from ..custom_model_form import CustomModelForm


logger = logging.getLogger(__name__)


def get_timezone_choices():
    """
    This method generates the options for the second timezone dropdown

    :return: A list of all available timezones
    :rtype: list
    """
    timezones = list(available_timezones())
    timezones.sort()
    return [("", "---------")] + [
        (tz, tz.split("/", 1)[1].replace("_", " ")) for tz in timezones if "/" in tz
    ]


def get_timezone_area_choices():
    """
    This method generates the options for the first timezone dropdown.
    It displays the general area of a country or city. Often the continent.

    :return: A list of the general areas of the timezones
    :rtype: list

    """
    timezone_regions = list(
        {
            tz.split("/")[0]
            for tz in available_timezones()
            if "/" in tz and "Etc" not in tz and "SystemV" not in tz
        }
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
        empty_label=_("Do no import initial content"),
        required=False,
    )

    timezone_area = forms.ChoiceField(
        choices=get_timezone_area_choices,
        label=_("Timezone area"),
        required=False,
    )

    deepl_midyear_start_enabled = forms.BooleanField(
        required=False,
        label=_("DeepL budget year start differs from renewal date"),
        help_text=__(
            _("Enable to set an add-on starting date differing from the renewal date."),
            format_deepl_help_text(
                _("Budget will be set as a monthly fraction of {} credits")
            ),
        ),
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
            "tunews_enabled",
            "timezone",
            "fallback_translations_enabled",
            "summ_ai_enabled",
            "hix_enabled",
            "deepl_renewal_month",
            "deepl_addon_booked",
            "deepl_midyear_start_month",
        ]
        #: The widgets which are used in this form
        widgets = {
            "timezone": forms.Select(choices=get_timezone_choices()),
            "icon": IconWidget(),
            "offers": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        r"""
        Initialize region form

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        super().__init__(*args, **kwargs)
        if self.instance and "/" in self.instance.timezone:
            self.fields["timezone_area"].initial = self.instance.timezone.split("/")[0]
        self.fields["slug"].required = False
        # Do not require coordinates because they might be automatically filled
        self.fields["latitude"].required = False
        self.fields["longitude"].required = False
        # Disable SUMM.AI option if locally and globally disabled
        if not settings.SUMM_AI_ENABLED and not (
            self.instance and self.instance.summ_ai_enabled
        ):
            self.fields["summ_ai_enabled"].disabled = True
        if not settings.TEXTLAB_API_ENABLED and not (
            self.instance and self.instance.hix_enabled
        ):
            self.fields["hix_enabled"].disabled = True
        self.fields["deepl_midyear_start_enabled"].initial = bool(
            self.instance.deepl_midyear_start_month
        )

    def save(self, commit=True):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :type commit: bool

        :return: The saved region object
        :rtype: ~integreat_cms.cms.models.regions.region.Region
        """

        # Only duplicate content if region is created and a region was selected
        duplicate_region = (
            not self.instance.id and self.cleaned_data["duplicated_region"]
        )

        # Save CustomModelForm
        region = super().save(commit=commit)

        if duplicate_region:
            source_region = self.cleaned_data["duplicated_region"]
            # Duplicate language tree
            logger.info("Duplicating language tree of %r to %r", source_region, region)
            duplicate_language_tree(source_region, region)
            # Disable linkcheck listeners to prevent links to be created for outdated versions
            with disable_listeners():
                # Duplicate pages
                logger.info("Duplicating page tree of %r to %r", source_region, region)
                duplicate_pages(source_region, region)
                # Duplicate Imprint
                logger.info("Duplicating imprint of %r to %r", source_region, region)
                duplicate_imprint(source_region, region)
            # Duplicate media content
            duplicate_media(source_region, region)
            # Create links for the most recent versions of all translations manually
            find_links(region)

        return region

    # pylint: disable=too-many-branches
    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()
        # Check whether statistics can be enabled
        if cleaned_data["statistics_enabled"] and not cleaned_data["matomo_token"]:
            self.add_error(
                "statistics_enabled",
                _(
                    "Statistics can only be enabled when a valid access token is supplied."
                ),
            )
        # Automatically set the Matomo ID
        if cleaned_data["matomo_token"]:
            try:
                cleaned_data["matomo_id"] = self.instance.statistics.get_matomo_id(
                    token_auth=cleaned_data["matomo_token"]
                )
            except MatomoException as e:
                logger.exception(e)
                self.add_error(
                    "matomo_token", _("The provided access token is invalid.")
                )
        else:
            cleaned_data["matomo_id"] = None

        # If DeepL budget year differs from renewal date is set, make sure a budget year start date is set
        if (
            cleaned_data["deepl_midyear_start_enabled"]
            and cleaned_data["deepl_midyear_start_month"] is None
        ):
            self.add_error(
                "deepl_midyear_start_month",
                _("Please provide a valid DeepL budget year start date."),
            )
        elif (
            not cleaned_data["deepl_midyear_start_enabled"]
            or cleaned_data["deepl_midyear_start_month"]
            == cleaned_data["deepl_renewal_month"]
        ):
            cleaned_data["deepl_midyear_start_month"] = None

        # Get additional data from GVZ API
        if apps.get_app_config("gvz_api").api_available:
            gvz_region = GvzRegion(
                region_name=cleaned_data["name"],
                region_ags=cleaned_data["common_id"],
                region_type=cleaned_data["administrative_division"],
            )
            logger.debug("GVZ API match: %r", gvz_region)
            if gvz_region.child_coordinates and not cleaned_data.get("aliases"):
                cleaned_data["aliases"] = gvz_region.child_coordinates
            if gvz_region.longitude and not cleaned_data.get("longitude"):
                cleaned_data["longitude"] = gvz_region.longitude
            if gvz_region.latitude and not cleaned_data.get("latitude"):
                cleaned_data["latitude"] = gvz_region.latitude
            if gvz_region.ags and not cleaned_data.get("common_id"):
                cleaned_data["common_id"] = gvz_region.ags

        # If the coordinates could not be filled automatically and have not been filled manually either, throw an error
        if not cleaned_data.get("latitude"):
            self.add_error(
                "latitude",
                forms.ValidationError(
                    _(
                        "Could not retrieve the coordinates automatically, please fill the field manually."
                    ),
                    code="required",
                ),
            )
        if not cleaned_data.get("longitude"):
            self.add_error(
                "longitude",
                forms.ValidationError(
                    _(
                        "Could not retrieve the coordinates automatically, please fill the field manually."
                    ),
                    code="required",
                ),
            )

        # Automatically fill the bounding box coordinates
        cleaned_data = self.autofill_bounding_box(cleaned_data)

        logger.debug("RegionForm validated [2] with cleaned data %r", cleaned_data)
        return cleaned_data

    def clean_slug(self):
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        :rtype: str
        """
        return generate_unique_slug_helper(self, "region")

    def clean_custom_prefix(self):
        """
        Validate the custom prefix field. (see :ref:`overriding-modelform-clean-method`)

        :return: The given prefix or ``None`` if it is invalid
        :rtype: str
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
                        map(str, administrative_divisions)
                    )
                # Check if custom prefix could also be set via the administrative division
                if (
                    cleaned_data.get("custom_prefix")
                    in translated_administrative_divisions
                ):
                    error_messages = []
                    # Get currently selected administrative division
                    selected_administrative_division = dict(
                        self.fields["administrative_division"].choices
                    )[cleaned_data.get("administrative_division")]
                    # Check if administrative division needs to be changed to translated version
                    if cleaned_data.get("custom_prefix") in administrative_divisions:
                        desired_administrative_division = cleaned_data.get(
                            "custom_prefix"
                        )
                    else:
                        # Get index of translated administrative division
                        index = translated_administrative_divisions.index(
                            cleaned_data.get("custom_prefix")
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
                                "'{}' is already selected as administrative division."
                            ).format(selected_administrative_division)
                        )
                    else:
                        error_messages.append(
                            _("Please select '{}' as administrative division.").format(
                                desired_administrative_division
                            )
                        )
                    # Check if default language needs to be changed in order to use this administrative division
                    if (
                        not self.instance.default_language
                        or self.instance.default_language.native_name != language_name
                    ):
                        error_messages.append(
                            _(
                                "Please set {} as default language for this region."
                            ).format(_(language_name))
                        )
                    # Check if administrative division is included in name yet
                    if not cleaned_data.get("administrative_division_included"):
                        error_messages.append(
                            _("Please enable '{}'.").format(
                                self.fields["administrative_division_included"].label
                            )
                        )
                    self.add_error(
                        "custom_prefix",
                        __(*error_messages),
                    )
        # Check if administrative division is also included in the name and allow only one of both prefix options
        if cleaned_data.get("custom_prefix") and cleaned_data.get(
            "administrative_division_included"
        ):
            self.add_error(
                "custom_prefix",
                _(
                    "You cannot include the administrative division into the name and use a custom prefix at the same time."
                ),
            )
        return cleaned_data.get("custom_prefix")

    def clean_aliases(self):
        """
        Validate the aliases field (see :ref:`overriding-modelform-clean-method`).

        :return: The valid aliases
        :rtype: dict
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

    def clean_summ_ai_enabled(self):
        """
        Validate the summ_ai_enabled field (see :ref:`overriding-modelform-clean-method`)

        :return: The validated field whether SUMM.AI is enabled
        :rtype: str
        """
        if self.cleaned_data.get("summ_ai_enabled") and not settings.SUMM_AI_ENABLED:
            self.add_error(
                "summ_ai_enabled", _("Currently SUMM.AI is globally deactivated")
            )
            return False
        return self.cleaned_data.get("summ_ai_enabled")

    def clean_hix_enabled(self):
        """
        Validate the hix_enabled field (see :ref:`overriding-modelform-clean-method`).

        :return: The validated field
        :rtype: bool
        """
        cleaned_hix_enabled = self.cleaned_data["hix_enabled"]
        # Check whether someone tries to activate hix when no API key is set
        if cleaned_hix_enabled and not settings.TEXTLAB_API_ENABLED:
            self.add_error(
                "hix_enabled", _("No Textlab API key is set on this system.")
            )
        return cleaned_hix_enabled

    @staticmethod
    def autofill_bounding_box(cleaned_data):
        """
        Automatically fill the bounding box coordinates

        :param cleaned_data: The partially cleaned data
        :type cleaned_data: dict

        :return: The updated cleaned data
        :rtype: dict
        """
        # When the Nominatim API is enabled, auto fill the bounding box coordinates
        if settings.NOMINATIM_API_ENABLED:
            nominatim_api_client = NominatimApiClient()
            bounding_box = nominatim_api_client.get_bounding_box(
                administrative_division=cleaned_data.get("administrative_division"),
                name=cleaned_data.get("name"),
                aliases=cleaned_data.get("aliases"),
            )
            if bounding_box:
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


def duplicate_language_tree(
    source_region,
    target_region,
    source_parent=None,
    target_parent=None,
    logging_prefix="",
):
    """
    Function to duplicate the language tree of one region to another.

    Usage: duplicate_language_tree(source_region, target_region)

    This is a recursive function to walk the whole language tree. It starts at root level with the default parent None.
    The recursion is necessary because the new nodes need their correct (also duplicated) parent node.

    :param source_region: The region from which the language tree should be duplicated
    :type source_region: ~integreat_cms.cms.models.regions.region.Region

    :param target_region: The region to which the language tree should be added
    :type target_region: ~integreat_cms.cms.models.regions.region.Region

    :param source_parent: The current parent node id of the recursion
    :type source_parent: ~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode

    :param target_parent: The node of the target region which is the duplicate of the source parent node
    :type target_parent: ~integreat_cms.cms.models.pages.page.Page

    :param logging_prefix: recursion level to get a pretty log output
    :type logging_prefix: str
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
            # If the target parent already exist, we inherit its tree id for all its sub nodes
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
        # Check if the resulting node is valid
        target_node.full_clean()
        # Save the duplicated node
        target_node.save()
        logger.debug(
            "%s Created target node %r",
            row_logging_prefix + ("└─" if source_node.is_leaf() else "├─"),
            target_node,
        )
        if not source_node.is_leaf():
            # Call the function recursively for all children of the current node
            duplicate_language_tree(
                source_region,
                target_region,
                source_node,
                target_node,
                row_logging_prefix,
            )


def duplicate_pages(
    source_region,
    target_region,
    source_parent=None,
    target_parent=None,
    logging_prefix="",
):
    """
    Function to duplicate all pages of one region to another.

    Usage: duplicate_pages(source_region, target_region)

    This is a recursive function to walk the whole page tree. It starts at root level with the default parent None.
    The recursion is necessary because the new pages need their correct (also duplicated) parent page.

    :param source_region: The region from which the pages should be duplicated
    :type source_region: ~integreat_cms.cms.models.regions.region.Region

    :param target_region: The region to which the pages should be added
    :type target_region: ~integreat_cms.cms.models.regions.region.Region

    :param source_parent: The current parent page id of the recursion
    :type source_parent: ~integreat_cms.cms.models.pages.page.Page

    :param target_parent: The page of the target region which is the duplicate of the source parent page
    :type target_parent: ~integreat_cms.cms.models.pages.page.Page

    :param logging_prefix: recursion level to get a pretty log output
    :type logging_prefix: str
    """

    logger.debug(
        "%s Duplicating child nodes",
        logging_prefix + "└─",
    )
    logging_prefix += "  "

    # At first, get all pages from the source region with a specific parent page
    # As the parent will be None for the initial call, this returns all pages from the root level
    source_pages = source_region.pages.filter(parent=source_parent)
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
        logger.debug(
            "%s Created %r",
            row_logging_prefix + "├─",
            target_page,
        )
        duplicate_page_translations(source_page, target_page, row_logging_prefix)
        if not source_page.is_leaf():
            # Recursively call this function with the current pages as new parents
            duplicate_pages(
                source_region,
                target_region,
                source_page,
                target_page,
                row_logging_prefix,
            )


def duplicate_page_translations(source_page, target_page, logging_prefix):
    """
    Duplicate all translations of a given source page to a given target page

    :param source_page: The given source page
    :type source_page: ~integreat_cms.cms.models.pages.page.Page

    :param target_page: The desired target page
    :type target_page: ~integreat_cms.cms.models.pages.page.Page

    :param logging_prefix: The prefix to be used for logging
    :type logging_prefix: str
    """
    logger.debug(
        "%s Duplicating page translations",
        logging_prefix + ("└─" if source_page.is_leaf() else "├─"),
    )
    # Clone all page translations of the source page
    source_page_translations = source_page.translations.all()
    num_translations = len(source_page_translations)
    translation_row_logging_prefix = logging_prefix + (
        "  " if source_page.is_leaf() else "│  "
    )
    for i, page_translation in enumerate(source_page_translations):
        # Set the page of the source translation to the new page
        page_translation.page = target_page
        # Delete the primary key to duplicate the object instance instead of updating it
        page_translation.pk = None
        # Set the translation to draft
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


def duplicate_imprint(source_region, target_region):
    """
    Function to duplicate the imprint from one region to another.

    :param source_region: the source region from which the imprint should be duplicated
    :type source_region: ~integreat_cms.cms.models.regions.region.Region

    :param target_region: the target region
    :type target_region: ~integreat_cms.cms.models.regions.region.Region

    """
    source_imprint = source_region.imprint
    target_imprint = deepcopy(source_imprint)
    target_imprint.region = target_region
    # Delete the primary key to duplicate the object instance instead of updating it
    target_imprint.pk = None
    # Check if the new imprint object is valid
    target_imprint.full_clean()

    target_imprint.save()

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


# pylint: disable=unused-argument
def duplicate_media(source_region, target_region):
    """
    Function to duplicate all media of one region to another.

    :param source_region: the source region from which the pages should be duplicated
    :type source_region: ~integreat_cms.cms.models.regions.region.Region

    :param target_region: the target region
    :type target_region: ~integreat_cms.cms.models.regions.region.Region

    """
    # TODO: implement duplication of all media files


def find_links(region):
    """
    Find all link objects in the latest versions of the region's page translations

    :param region: The region which should be scanned for links
    :type region: ~integreat_cms.cms.models.regions.region.Region
    """
    logger.info("Scanning for broken links in region %r", region)
    # Get the latest page translations of the region
    translations = PageTranslation.objects.filter(page__region=region).distinct(
        "page_id", "language_id"
    )
    # Trigger post-save signal to create link objects
    for translation in translations:
        translation.save(update_timestamp=False)
    # Check whether finding links succeeded
    logger.debug(
        "Found links: %r", Link.objects.filter(Q(page_translation__page__region=region))
    )
