import logging
import json
import sys
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class GvzApiWrapper():
    """
    Class that wraps around the GVZ API
    """
    api_url = settings.GVZ_API_URL

    def search(self, region_name):
        """
        Search for a location and return candidates
        """

        logger.debug("Searching for {}".format(region_name))
        r = requests.get("https://gvz.integreat-app.de/api/searchcounty/{}".format(sys.argv[-1]))
        regions = json.loads(r.content)
        return regions

    def get_details(self, region_key):
        """
        Get details (name, longitude, latitude, children) for a region key
        """
        r = requests.get("https://gvz.integreat-app.de/api/details/{}".format(region_key))
        location = json.loads(r.content)[0]
        if ',' in location['name']:
            location['name'] = location['name'].split(',')[0]
        return {
            "longitude": location['longitude'],
            "latitude": location['latitude']
        }

    def search_single_match(self):
        """
        Tries to find the correct region (single search hit)
        """
        pass


class GvzRegion():
    """
    Represents a region in the GVZ
    """
    key = 0
    name = ""
    longitude = ""
    latitude = ""
    children = []

    def __init__(self, region_key=0, region_name=""):
        """
        Get values from API
        """
        if region_key:  # load data
            pass
        if region_name:  # find best match and load data
            pass

    def __dict__(self):
        """
        Dictionary representation of region
        """
        return {
            "name": str(self),
            "longitude": self.longitude,
            "latitude": self.latitude,
            "children": self.children
        }

    def __str__(self):
        """
        String representation of region
        """
        return self.name
