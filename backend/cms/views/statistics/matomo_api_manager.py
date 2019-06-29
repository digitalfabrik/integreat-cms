"""
Helper class to interact with the Matomo API
"""
import re
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class MatomoApiManager:
    """
    This class helps to interact with Matomo API
    There are several functions to retrieve unique visitors for last 30 days,
    a month, and a year.
    You are also able to add new sites to your matomo instance and furthermore.
    """

    protocol = "https://"  # Protocol "http://" or "https://"
    """
    Variable which allows you also to accept broken ssl-certificates with
    requests library (False == ignore ssl-issues, True == dont allow broken
    ssl-certificates
    """
    ssl_verify = True
    matomo_url = ""  # URL to Matomo-Instance
    matomo_api_key = ""  # Matomo API-key

    def __init__(self, matomo_url, matomo_api_key, ssl_verify):
        """
        Constructor initialises matomo_url, matomo_api_key, ssl_verify
        :param matomo_url:
        :param matomo_api_key:
        :param ssl_verify:
        """
        self.matomo_url = matomo_url
        self.matomo_api_key = matomo_api_key
        self.matomo_api_key = "&token_auth=" + self.matomo_api_key  # concats token api-parameter
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
        elif not bool(re.match("^https://", self.matomo_url)):  # check for "https://" and set it
            self.matomo_url = self.protocol + self.matomo_url

    def checkmatomo_url(self):
        """
        This method checks the proper functionality of a simple url request
        :return: True or False
        """
        try:
            http_code = requests.get(self.matomo_url, verify=self.ssl_verify).status_code
            if http_code == 200:
                return True
            return False
        except ConnectionError:
            return False

    def get_visitors_per_timerange(self, date_string, site_id, period, lang):
        """
        Returns the total unique visitors in a timerange as definded in period
        :param site_id: String
        :param date_string: String "yyyy-mm-dd,yyyy-mm-dd"
        :param period: String "day", "week", "month", "year"
        :param lang: String contains the language, that is called
        :return: List[Date, Hits]
        """
        domain = self.matomo_url
        api_key = self.matomo_api_key
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'From': 'holtgrave@integreat-app.de'  # This is another valid field
        }
        response = {}
        url = """{}/index.php?date={}&expanded=1
        &filter_limit=-1&format=JSON&format_metrics=1
        &idSite={}&method=API.get&module=API&period={}
        &segment=pageUrl%253D@%25252F{}
        %25252Fwp-json%25252F{}""".format(domain, date_string, site_id, period, lang, api_key)

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        response = session.get(url).json()

        result = []
        for json_object in response:
            if period == "day":
                if response[json_object] == []:
                    result.append([re.sub(r'(\d{4})-(\d{1,2})-(\d{1,2})',
                                          '\\3-\\2-\\1', json_object), 0])
                else:
                    result.append([re.sub(r'(\d{4})-(\d{1,2})-(\d{1,2})',
                                          '\\3-\\2-\\1', json_object),
                                   response[json_object]['nb_uniq_visitors']])
            elif period == "month":
                if response[json_object] == []:
                    result.append([re.sub(r'(\d{4})-(\d{1,2})',
                                          '\\2-\\1', json_object), 0])
                else:
                    result.append([re.sub(r'(\d{4})-(\d{1,2})',
                                          '\\2-\\1', json_object),
                                   response[json_object]['nb_uniq_visitors']])
        return result
