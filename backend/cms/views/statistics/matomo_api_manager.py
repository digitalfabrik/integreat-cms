"""
Helper class to interact with the Matomo API
"""
import re
import json
import requests


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

    def api_request(self, method, curl):
        """
        General function which will handle requests to the api and exceptions for all functions
        :param method: get- or push-http-request, shoud be a string
        :param curl: concated protocoll with matomo_url, api-method and matomo_api_key
        :return: returns api reply
        """
        try:
            if method == "get":
                request = requests.get(curl, verify=self.ssl_verify)
            elif method == "push":  # not used so far
                request = requests.get(curl, verify=self.ssl_verify)
        except ConnectionError:
            request = False
        return request.text

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

    def create_instance(self, site_name, url, timezone, start_date):
        """
        Creates an instance on Matomo-instance.
        :param site_name: String
        :param url: String
        :param timezone: String "utc-1" for Germany/Berlin
        :param start_date: String "yyyy-mm-dd" or e.g. "2007-07-24"
        :return: String ID of newly created instance
        """
        method = "/?module=API&method=SitesManager.addSite&site_name=" + site_name + "&urls=" + url
        method += "&timezone=" + timezone + "&start_date=" + start_date
        curl = self.matomo_url + method + self.matomo_api_key
        request = self.api_request("get", curl)
        return request

    def get_all_site_ids(self):
        """
        Returns only all siteIDs
        :return: JSON with all IDs
        """
        method = "/?module=API&method=SitesManager.getAllSitesId&format=JSON"
        curl = self.matomo_url + method + self.matomo_api_key
        request = self.api_request("get", curl)

        return request

    def get_all_sites_id_name(self):  # Site ID und Site Name
        """
        Returns SiteIDs with the instance name as a list object
        :return: list object
        """
        method = "/?module=API&method=SitesManager.getAllSites&format=JSON"
        curl = self.matomo_url + method + self.matomo_api_key
        request = self.api_request("get", curl)

        request = json.loads(request)

        name_list = []

        i = 0
        for json_object in request:
            list.append([])
            for (key, value) in json_object.items():
                if key == "idsite":
                    name_list[i].append(value)
                if key == "name":
                    name_list[i].append(value)
            i += 1
        return name_list

    def get_all_sites(self):
        """
        Returns all instances of your matomo instance and all metadata of it
        :return: JSON
        """
        method = "/?module=API&method=SitesManager.getAllSites&format=json"
        curl = self.matomo_url + method + self.matomo_api_key
        request = self.api_request("get", curl)
        return request

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
        response = {}
        url = """{}/index.php?date={}&expanded=1
        &filter_limit=-1&format=JSON&format_metrics=1
        &idSite={}&method=API.get&module=API&period={}
        &segment=pageUrl%253D@%25252F{}
        %25252Fwp-json%25252F{}""".format(domain, date_string, site_id, period, lang, api_key)
        response = requests.get(url).json()
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
