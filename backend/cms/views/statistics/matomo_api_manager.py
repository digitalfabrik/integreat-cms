#!/usr/bin/env python3
"""
Helper class to interact with the Matomo API
"""
from datetime import datetime, timedelta
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

    def __init__(self, matomo_URL, matomo_api_key, ssl_verify):
        """
        Constructor initialises matomo_url, matomo_api_key, ssl_verify
        :param matomo_url:
        :param matomo_api_key:
        :param ssl_verify:
        """
        self.matomo_url = matomo_URL
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

    def get_unique_visitors(self, site_id, date, period):
        """
        Delivers unique visiors for a period ("day", "week", "month", "year") from beginning date
        :param site_id: String
        :param date: String "yyyy-mm-dd" or e.g. "2019-07-24"
        :param period: String "day", "week", "month", "year"
        :return: String cumulated unique visitors
        """
        method = "/?module=API&method=VisitsSummary.getUniqueVisitors&idSite=" + site_id
        method += "&period=" + period + "&date=" + date + "&format=JSON"
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

    def get_unique_visitors_per_day(self, date, site_id, lang):
        """
        Returns unique visitors per day
        :param date: String "yyyy-mm-dd" or e.g. "2007-07-24"
        :param site_id: String
        :param lang: String e.g. "de" for german, "en" for english
        :return: List with date and count of unique visitors for this date
        """
        method = "/index.php?date=" + date + "&expanded=1&filter_limit=-1&format=JSON"
        method += "&format_metrics=1" + "&idSite=" + site_id
        method += "&method=API.get&module=API&period=day&segment=pageUrl%253D@%25252F"
        method += lang + "%25252Fwp-json%25252F"
        curl = self.matomo_url + method + self.matomo_api_key
        request = self.api_request("get", curl)
        request = json.loads(request)
        list_hits = []

        list_hits.append(date)
        for (key, value) in request.items():
            if key == "nb_uniq_visitors":
                list_hits.append(value)
        return list_hits

    def get_unique_visitors_month(self, year, month, site_id, lang):  # month should be 01 for Jan
        """
        Unique visitors for whole month in requested year
        :param year: String "YYYY" or e.g. "2019"
        :param month: String "MM" or e.g. "02" for February
        :param site_id: String
        :param lang: String e.g. "de" for german, "en" for english
        :return:
        """
        start_date = datetime(int(year), int(month), 1).date()
        end_date = self.last_day_of_month(datetime(int(year), int(month), 1).date())

        delta = end_date - start_date
        list_hits = []
        for i in range(delta.days+1):
            date = start_date + timedelta(i)
            list_hits.append(self.get_unique_visitors_per_day(date.strftime('%Y-%m-%d'),
                                                              site_id, lang))
        return list_hits

    def get_unique_visitors_year(self, year, site_id, lang):  # year in format as "2019"
        """
        Returns unique visitors for a all days in a whole year
        :param year: String "YYYY" or e.g. "2019"
        :param site_id: String
        :param lang: String e.g. "de" for german, "en" for english
        :return: List with dates and count of unique visitors for all dates in a year
        """
        start_date = datetime(int(year), 1, 1).date()
        end_date = self.last_day_of_month(datetime(int(year), 12, 1).date())

        delta = end_date - start_date
        list_hits = []
        for i in range(delta.days+1):
            date = start_date + timedelta(i)
            list_hits.append(self.get_unique_visitors_per_day(date.strftime('%Y-%m-%d'), site_id,
                                                              lang))
        return list_hits

    def get_unique_visitors_last_30(self, site_id, lang):
        """
        Returns unique visitors for last 30 days since today
        :param site_id: String
        :param lang: String e.g. "de" for german, "en" for english
        :return: List with dates and count of unique visitors for last 30 days
        """
        start_date = datetime.now().date() + timedelta(-30)
        end_date = datetime.now().date()

        delta = end_date - start_date
        list_hits = []
        for i in range(delta.days+1):
            date = start_date + timedelta(i)
            list_hits.append(self.get_unique_visitors_per_day(date.strftime('%Y-%m-%d'),
                                                              site_id, lang))
        return list_hits

    def get_timezones_list(self):
        """
        Shows you all possible Timezones with utc codes.
        :return: JSON
        """
        method = "/?module=API&method=SitesManager.getTimezonesList"
        curl = self.matomo_url + method + self.matomo_api_key
        request = self.api_request("get", curl)
        return request

    @staticmethod
    def last_day_of_month(any_month):
        """
        Calculates last day of month helps severy other methods in finding proper dates.
        Thanks and CC to Augusto Men on Stackoverflow
        :param any_month: Date for which last day will be calculated
        :return: Date last day of month
        """
        next_month = any_month.replace(day=28) + timedelta(days=4)  # this will never fail
        return next_month - timedelta(days=next_month.day)
