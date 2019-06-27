"""Views related to the statistics module"""
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from .matomo_api_manager import MatomoApiManager
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class AnalyticsView(TemplateView):
    """
    Class to create the statistic page, that can be found via -> "Statistiken"
    """
    template_name = 'statistics/statistics_dashboard.html'
    base_context = {'current_menu_item': 'statistics'}

    @staticmethod
    def prepare_csv(languages, hits, dates):
        """
        Method to create CSV String from the API hits
        """
        csv_row = "date"
        csv_raw = ""
        for l_value in languages:
            csv_row += "," + l_value[1]
        csv_raw += csv_row + ";"
        for date_index, _ in enumerate(dates):
            csv_row = ""
            csv_row += str(dates[date_index]) + ","
            for idy in range(0, len(languages)):
                csv_row += str(hits[idy][2][date_index])
                if idy < (len(languages) - 1):
                    csv_row += ","
            csv_row += ";"
            csv_raw += str(csv_row)
        return csv_raw

    def get(self, request, *args, **kwargs):
        start_date = request.GET.get('start_date', str(date.today() -
                                                       timedelta(days=30)))
        end_date = request.GET.get('end_date', str(date.today()))
        languages = [["de", "Deutsch", "#7e1e9c"], ["en", "Englisch", "#15b01a"],
                     ["ar", "Arabisch", "#0343df"]]

        api_man = MatomoApiManager(matomo_url="https://statistics.integreat-app.de",
                                   matomo_api_key="",
                                   ssl_verify=True)
        response_dates = []
        response_hits = []
        for lang in languages:
            api_hits = api_man.get_visitors_per_timerange(date_string=start_date + ',' + end_date,
                                                          site_id="2",
                                                          period=request.GET.get('peri', 'day'),
                                                          lang=lang[0])
            temp_hits = []
            for single_day in api_hits:
                temp_hits.append(single_day[1])
            response_hits.append([lang[1], lang[2], temp_hits])
        for single_day in api_hits:
            response_dates.append(single_day[0])

        return render(request, self.template_name,
                      {**self.base_context,
                       'csv': self.prepare_csv(languages, response_hits, response_dates),
                       'dates': response_dates,
                       'hits': response_hits})
