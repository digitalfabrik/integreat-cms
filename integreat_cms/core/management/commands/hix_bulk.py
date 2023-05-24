import logging
import time

from django.conf import settings
from django.core.management.base import CommandError
from linkcheck.listeners import disable_listeners

from ....cms.models import Region
from ..log_command import LogCommand

logger = logging.getLogger(__name__)


def calculate_hix_for_region(region):
    """
    Calculates the hix score for all missing pages in the region.
    Assumes that hix is globally enabled and enabled for the region

    :param region: The region
    :type region: ~integreat_cms.cms.models.regions.region.Region
    """
    for page in region.pages.all().prefetch_translations(
        to_attr="prefetched_textlab_translations",
        language__slug__in=settings.TEXTLAB_API_LANGUAGES,
    ):
        for translation in page.prefetched_textlab_translations:
            if translation.hix_score is not None:
                logger.debug(
                    "skipping %r: Already has a hix score of %s",
                    translation,
                    translation.hix_score,
                )
                continue
            if not translation.content.strip():
                logger.debug("skipping %r: Empty content", translation)
                continue

            translation.save(update_timestamp=False)
            time.sleep(settings.TEXTLAB_API_BULK_WAITING_TIME)


class Command(LogCommand):
    """
    Command to calculate the hix values for public page translations which do not currently have a score
    """

    help = "Calculates and stores the hix value for all public page translations for which it is missing"

    def add_arguments(self, parser):
        """
        Define the arguments of this command

        :param parser: The argument parser
        :type parser: ~django.core.management.base.CommandParser
        """
        parser.add_argument(
            "region_slugs",
            help="The slugs of the regions which should be processed. If empty, all regions will be processed",
            nargs="*",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args, region_slugs, **options):
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :type \*args: list

        :param region_slugs: The slugs of the given regions
        :type region_slugs: list

        :param \**options: The supplied keyword options
        :type \**options: dict
        """
        if not settings.TEXTLAB_API_ENABLED:
            raise CommandError("HIX API is globally disabled")

        if not region_slugs:
            regions = Region.objects.filter(hix_enabled=True)
        else:
            regions = Region.objects.filter(slug__in=region_slugs)
            if len(regions) != len(region_slugs):
                diff = set(region_slugs) - set(region.slug for region in regions)
                raise CommandError(f"The following regions do not exist: {diff}")

        # Disable linkcheck listeners to prevent links to be created for outdated translations
        with disable_listeners():
            for region in regions:
                if not region.hix_enabled:
                    logger.warning("HIX is disabled for %r", region)
                    continue

                logger.info("Processing region %r", region)
                calculate_hix_for_region(region)
                self.print_info(
                    f"Waiting for {settings.TEXTLAB_API_BULK_COOL_DOWN_PERIOD}s to cool down"
                )
                time.sleep(settings.TEXTLAB_API_BULK_COOL_DOWN_PERIOD)

        self.print_success("Done")
