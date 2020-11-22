"""
Helper class to interact with the Matomo API
"""
import re
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class MatomoApiManager:
    """
    This class helps to interact with Matomo API.
    There are several functions to retrieve unique visitors for last 30 days, a month, and a year.
    You are also able to add new regions to your matomo instance and furthermore.
    """

    #: HTTP Protocol: "http://" or "https://"
    protocol = "https://"
    #: Variable which allows you also to accept broken SSL-certificates with requests library (``False`` means: ignore
    #: SSL-issues, ``True`` means: don't allow broken SSL-certificates)
    ssl_verify = True
    #: URL to Matomo-Instance
    matomo_url = ""
    #: Matomo API-key
    matomo_api_key = ""

    def __init__(self, matomo_url, matomo_api_key, ssl_verify):
        """
        Constructor initialises matomo_url, matomo_api_key and ssl_verify

        :param matomo_url: URL to Matomo-Instance
        :type matomo_url: str

        :param matomo_api_key: Matomo API-key
        :type matomo_api_key: str

        :param ssl_verify: Whether to check for broken SSL-certificates
        :type ssl_verify: bool
        """

        self.matomo_url = matomo_url
        self.matomo_api_key = matomo_api_key
        self.matomo_api_key = (
            "&token_auth=" + self.matomo_api_key
        )  # concats token api-parameter
        self.ssl_verify = ssl_verify
        self.cleanmatomo_url()  # cleans matomo url for proper requests

    def cleanmatomo_url(self):
        """
        Cleans Matomo-URL for proper requests.
        Checks ending slash and beginning http(s)://
        """

        self.matomo_url = re.sub(r"/\/$/", "", self.matomo_url)  # Cuts "/"

        if re.match(r"^http://", self.matomo_url):  # replace it to "https://"
            self.matomo_url = re.sub("^http://", "", self.matomo_url)
            self.matomo_url = self.protocol + self.matomo_url
        elif not bool(
            re.match("^https://", self.matomo_url)
        ):  # check for "https://" and set it
            self.matomo_url = self.protocol + self.matomo_url

    def checkmatomo_url(self):
        """
        This method checks the proper functionality of a simple url request

        :return: Whether or not Matomo is available
        :rtype: bool
        """

        try:
            http_code = requests.get(
                self.matomo_url, verify=self.ssl_verify
            ).status_code
            if http_code == 200:
                return True
            return False
        except ConnectionError:
            return False

    def get_visitors_per_timerange(self, date_string, region_id, period, lang):
        """
        Returns the total unique visitors in a timerange as definded in period

        :param date_string: Time range in the format ``"yyyy-mm-dd,yyyy-mm-dd"``
        :type date_string: str

        :param region_id: The id of the requested region
        :type region_id: str

        :param period: The period (e.g. ``"day"``, ``"week"``, ``"month"`` or ``"year"``)
        :type period: str

        :param lang: The requested language code
        :type lang: str

        :return: List of visitors in the requested time range
        :rtype: list
        """

        domain = self.matomo_url
        api_key = self.matomo_api_key
        url = f"""{domain}/index.php?date={date_string}&expanded=1
        &filter_limit=-1&format=JSON&format_metrics=1
        &idSite={region_id}&method=API.get&module=API&period={period}
        &segment=pageUrl%253D@%25252F{lang}
        %25252Fwp-json%25252F{api_key}"""

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        response = session.get(url).json()

        result = []
        for json_object in response:
            if period == "day":
                if response[json_object] == []:
                    result.append(
                        [
                            re.sub(
                                r"(\d{4})-(\d{1,2})-(\d{1,2})",
                                "\\3-\\2-\\1",
                                json_object,
                            ),
                            0,
                        ]
                    )
                else:
                    result.append(
                        [
                            re.sub(
                                r"(\d{4})-(\d{1,2})-(\d{1,2})",
                                "\\3-\\2-\\1",
                                json_object,
                            ),
                            response[json_object]["nb_uniq_visitors"],
                        ]
                    )
            elif period == "month":
                if response[json_object] == []:
                    result.append(
                        [re.sub(r"(\d{4})-(\d{1,2})", "\\2-\\1", json_object), 0]
                    )
                else:
                    result.append(
                        [
                            re.sub(r"(\d{4})-(\d{1,2})", "\\2-\\1", json_object),
                            response[json_object]["nb_uniq_visitors"],
                        ]
                    )
        return result
