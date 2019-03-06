"""Views related to the statistics module"""
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render
import requests


@method_decorator(login_required, name='dispatch')
class AnalyticsView(TemplateView):
    template_name = 'statistics/statistics_dashboard.html'
    base_context = {'current_menu_item': 'statistics'}

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})


def statistics_data(request):
    # lang = ['de', 'en', 'fr', 'ar', 'fa']
    url = "https://statistics.integreat-app.de/index.php"
    # start_date = request.GET.get('start_date', datetime.utcnow)
    # end_date = request.GET.get('end_date', str(datetime.utcnow)
    date_range = "?date=2019-01-04,2019-02-19"
    site_id = "&idSite=2"
    params = "&expanded=1&filter_limit=100&format=JSON&format_metrics=1&method=API.get&module=API&period=day"
    token = "&token_auth=cf98cbb69aa84a184621cd2fa287d960"
    response = requests.get(url + date_range + site_id + params + token)
    return HttpResponse(response.text)
