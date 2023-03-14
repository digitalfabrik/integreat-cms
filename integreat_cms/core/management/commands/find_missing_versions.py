import logging
from argparse import ArgumentTypeError

from ....cms.models import EventTranslation, PageTranslation, POITranslation
from ..log_command import LogCommand

logger = logging.getLogger(__name__)

#: The possible model choices
MODELS = {"page": PageTranslation, "event": EventTranslation, "poi": POITranslation}


def get_model(model_str):
    """
    Convert a model string to a translation model class

    :param model_str: The model string
    :type model_str: str

    :return: The model class
    :rtype: type

    :raises ~argparse.ArgumentTypeError: When the input is invalid
    """
    try:
        return MODELS[model_str]
    except KeyError as e:
        raise ArgumentTypeError(
            "Invalid model (must be either page, event or poi)"
        ) from e


class Command(LogCommand):
    """
    Management command to find missing versions
    """

    help = "Find version inconsistencies in the CMS"

    def add_arguments(self, parser):
        """
        Define the arguments of this command

        :param parser: The argument parser
        :type parser: ~django.core.management.base.CommandParser
        """
        parser.add_argument(
            "model",
            type=get_model,
            help="The model to check",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args, model, **options):
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :type \*args: list

        :param model: The model to check
        :type model: type

        :param \**options: The supplied keyword options
        :type \**options: dict
        """
        self.print_info(
            f"Checking the model {model.__name__} for version inconsistencies..."
        )
        success = True
        for latest_version in model.objects.distinct(
            f"{model.foreign_field()}__pk", "language__pk"
        ):
            num = latest_version.foreign_object.translations.filter(
                language=latest_version.language
            ).count()
            if latest_version.version != num:
                self.print_error(
                    f"The latest version of {latest_version.foreign_object!r} in {latest_version.language!r} is {latest_version.version}, but there are only {num} translation objects!"
                )
                success = False
        if success:
            self.print_success("✔ All versions are consistent.")
