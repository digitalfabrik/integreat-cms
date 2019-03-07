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

    data = [1, 2, 3, 4, 5, 6, 8]

    def get(self, request, *args, **kwargs):
        from_date = request.GET.get('start_date', str(date.today() - timedelta(days=30)))
        to_date = request.GET.get('end_date', str(date.today()))
        view = request.GET.get('viewselection', 'monthly')
        data = view + from_date + to_date
        return render(request, self.template_name,
                      {**self.base_context,
                       'data': data})
