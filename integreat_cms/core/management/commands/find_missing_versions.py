from __future__ import annotations

import logging
from argparse import ArgumentTypeError
from typing import TYPE_CHECKING

from ....cms.models import EventTranslation, PageTranslation, POITranslation
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser
    from django.db.models.base import ModelBase

logger = logging.getLogger(__name__)

#: The possible model choices
MODELS: dict[str, ModelBase] = {
    "page": PageTranslation,
    "event": EventTranslation,
    "poi": POITranslation,
}


def get_model(model_str: str) -> ModelBase:
    """
    Convert a model string to a translation model class

    :param model_str: The model string
    :return: The model class
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

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "model",
            type=get_model,
            help="The model to check",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args: Any, model: ModelBase, **options: Any) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param model: The model to check
        :param \**options: The supplied keyword options
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
