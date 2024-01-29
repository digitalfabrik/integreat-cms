"""
Utilities for the Nominatim API app
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from geopy.location import Location

logger = logging.getLogger(__name__)


class BoundingBox:
    """
    Class for bounding boxes
    """

    def __init__(
        self,
        latitude_min: float,
        latitude_max: float,
        longitude_min: float,
        longitude_max: float,
    ) -> None:
        """
        Initialize the bounding box

        :param latitude_min: The bottom boundary of the box
        :param latitude_max: The top boundary of the box
        :param longitude_min: The left boundary of the box
        :param longitude_max: The right boundary of the box
        """
        self.latitude_min = latitude_min
        self.latitude_max = latitude_max
        self.longitude_min = longitude_min
        self.longitude_max = longitude_max

    @property
    def api_representation(self) -> list[list[float]]:
        """
        The bounding box in the format::

            [
                [
                    longitude_min,
                    latitude_min
                ],
                [
                    longitude_max,
                    latitude_max
                ]
            ]

        :return: A nested list of the borders of the box
        """
        return [
            [self.longitude_min, self.latitude_min],
            [self.longitude_max, self.latitude_max],
        ]

    @classmethod
    def from_result(cls, result: Location | None) -> BoundingBox | None:
        """
        Return a bounding box object from a Nominatim API result

        :param result: The Nominatim API result
        :return: A bounding box
        """
        # The order of the bounding box fields match the order of the fields in the __init__ method.
        return cls(*result.raw["boundingbox"]) if result else None

    @classmethod
    def merge(cls, *bounding_boxes: BoundingBox | None) -> BoundingBox | None:
        r"""
        Merge the given bounding boxes

        :param \*bounding_boxes: The bounding boxes that should be merged
        :return: A bounding box that contains all of the given boxes
        """
        # Filter out empty boxes
        if bounding_boxes := tuple(filter(None, bounding_boxes)):
            logger.debug("Merging bounding boxes: %r", bounding_boxes)
            # Return a new bounding box with the minimum/maximum values over all given bounding boxes
            return cls(
                min(box.latitude_min for box in bounding_boxes),
                max(box.latitude_max for box in bounding_boxes),
                min(box.longitude_min for box in bounding_boxes),
                max(box.longitude_max for box in bounding_boxes),
            )
        # If an empty list was given, return None
        return None

    def __repr__(self) -> str:
        """
        String representation for debug logging

        :return: The canonical representation of the object
        """
        return f"<BoundingBox(longitude_min: {self.longitude_min}, latitude_min: {self.latitude_min}, longitude_max: {self.longitude_max}, latitude_max: {self.latitude_max}])>"
