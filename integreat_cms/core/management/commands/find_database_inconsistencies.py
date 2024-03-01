from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.db.models import OuterRef, Q, Subquery

from ....cms.models import (
    EventTranslation,
    LanguageTreeNode,
    Page,
    PageTranslation,
    POITranslation,
)
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser
    from django.db.models.base import ModelBase

logger = logging.getLogger(__name__)

#: The possible translation model choices
VERSION_MODELS: list[ModelBase] = {
    PageTranslation,
    EventTranslation,
    POITranslation,
}

#: The possible tree model choices
TREE_MODELS: list[ModelBase] = {
    Page,
    LanguageTreeNode,
}


class Command(LogCommand):
    """
    Management command to find missing versions
    """

    help = "Find version inconsistencies in the CMS"

    def find_tree_inconsistencies(self):
        """
        Find inconsistencies in MPTT structure
        """
        for model in TREE_MODELS:
            self.print_info(
                f"Checking the model {model.__name__} for tree inconsistencies..."
            )
            inconsistencies = model.objects.filter(
                Q(
                    lft__in=Subquery(
                        model.objects.filter(tree_id=OuterRef("tree_id")).values_list(
                            "rgt", flat=True
                        )
                    )
                )
                | Q(
                    rgt__in=Subquery(
                        model.objects.filter(tree_id=OuterRef("tree_id")).values_list(
                            "lft", flat=True
                        )
                    )
                )
            )
            if len(inconsistencies):
                self.print_error("Oh oh, there are tree inconsistencies!")
                for i in inconsistencies:
                    if (lft := inconsistencies.filter(tree_id=i.tree_id, rgt=i.lft).first()):
                        self.print_error(
                            f"{i!r} has the same lft value ({i.lft}) as the rgt of {lft!r}"
                        )
                    if (rgt := inconsistencies.filter(tree_id=i.tree_id, lft=i.rgt).first()):
                        self.print_error(
                            f"{i!r} has the same rgt value ({i.rgt}) as the lft of {rgt!r}"
                        )

            else:
                self.print_success(
                    f"✔ All trees of model {model.__name__} are consistent."
                )

    def find_missing_versions(self):
        """
        Find missing versions in content translations
        """
        for model in VERSION_MODELS:
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
                self.print_success(
                    f"✔ All versions of model {model.__name__} are consistent."
                )

    def handle(self, *args: Any, **options: Any) -> None:
        r"""
        Try to run the command
        """
        self.find_missing_versions()
        self.find_tree_inconsistencies()
