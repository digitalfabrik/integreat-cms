from django.views.generic import TemplateView


class EvaluationListView(TemplateView):
    template_name = "evaluation/evaluation_list.html"
