"""
Utilities for the Nominatim API app
"""
import logging

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class BoundingBox:
    """
    Class for bounding boxes
    """

    def __init__(self, latitude_min, latitude_max, longitude_min, longitude_max):
        """
        Initialize the bounding box

        :param latitude_min: The bottom boundary of the box
        :type latitude_min: float

        :param latitude_max: The top boundary of the box
        :type latitude_max: float

        :param longitude_min: The left boundary of the box
        :type longitude_min: float

        :param longitude_max: The right boundary of the box
        :type longitude_max: float
        """
        self.latitude_min = latitude_min
        self.latitude_max = latitude_max
        self.longitude_min = longitude_min
        self.longitude_max = longitude_max

    @property
    def api_representation(self):
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
        :rtype: [ [ float, float ], [ float, float ] ]
        """
        return [
            [self.longitude_min, self.latitude_min],
            [self.longitude_max, self.latitude_max],
        ]

    @classmethod
    def from_result(cls, result):
        """
        Return a bounding box object from a Nominatim API result

        :param result: The Nominatim API result
        :type result: geopy.location.Location

        :return: A bounding box
        :rtype: ~integreat_cms.nominatim_api.utils.BoundingBox
        """
        if not result:
            return None
        # The order of the bounding box fields match the order of the fields in the __init__ method.
        return cls(*result.raw["boundingbox"])

    @classmethod
    def merge(cls, *bounding_boxes):
        r"""
        Merge the given bounding boxes

        :param \*bounding_boxes: The bounding boxes that should be merged
        :type \*bounding_boxes: list [ ~integreat_cms.nominatim_api.utils.BoundingBox ]

        :return: A bounding box that contains all of the given boxes
        :rtype: ~integreat_cms.nominatim_api.utils.BoundingBox
        """
        # Filter out empty boxes
        bounding_boxes = list(filter(None, bounding_boxes))
        # If an empty list was given, return None
        if not bounding_boxes:
            return None
        logger.debug("Merging bounding boxes: %r", bounding_boxes)
        # Return a new bounding box with the minimum/maximum values over all given bounding boxes
        return cls(
            min(box.latitude_min for box in bounding_boxes),
            max(box.latitude_max for box in bounding_boxes),
            min(box.longitude_min for box in bounding_boxes),
            max(box.longitude_max for box in bounding_boxes),
        )

    def __repr__(self):
        """
        String representation for debug logging

        :return: The canonical representation of the object
        :rtype: str
        """
        return f"<BoundingBox(longitude_min: {self.longitude_min}, latitude_min: {self.latitude_min}, longitude_max: {self.longitude_max}, latitude_max: {self.latitude_max}])>"
