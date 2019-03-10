"""Views related to the statistics module"""
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render


@method_decorator(login_required, name='dispatch')
class AnalyticsView(TemplateView):
    template_name = 'statistics/statistics_dashboard.html'
    base_context = {'current_menu_item': 'statistics'}
    dates = ["Januar", "Februar", "März", "April", "May"]
    lang = ["Deutsch", "Englisch", "Arabisch"]
    color = ["#7e1e9c", "#15b01a", "#0343df", "#e50000", "#95d0fc", "#029386", "#f97306", "#96f97b", "#c20078", "#ffff14", "#75bbfd", "#89fe05", "#bf77f6", "#9a0eea", "#033500", "#06c2ac", "#00035b", "#d1b26f", "#00ffff"]
    raw_hits = [[200, 100, 50, 40, 20], [250, 150, 40, 30, 20], [350, 250, 4, 35, 25]]
    hits = [[lang[0], color[0], raw_hits[0]], [lang[1], color[1], raw_hits[1]], [lang[2], color[2], raw_hits[2]]]

    csv_row = "date"
    csv_raw = ""
    for l in lang:
        csv_row += "," + l
    csv_raw += csv_row + ";"
    for date in range(0, len(lang)):
        csv_row = ""
        csv_row += str(dates[date]) + ","
        for idy in range(0, len(lang)):
            csv_row += str(raw_hits[idy][date])
            if idy < (len(lang) - 1):
                csv_row += ","
        csv_row += ";"
        csv_raw += str(csv_row)

    def get(self, request, *args, **kwargs):
        from_date = request.GET.get('start_date', str(date.today() -
                                                      timedelta(days=30)))
        to_date = request.GET.get('end_date', str(date.today()))
        view = request.GET.get('viewselection', 'monthly')
        param = view + from_date + to_date
        return render(request, self.template_name,
                      {**self.base_context,
                       'csv': self.csv_raw,
                       'param': param,
                       'dates': self.dates, 'hits': self.hits})
