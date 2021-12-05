from django.urls import path
from django.views.generic import TemplateView

app_name = "help"

urlpatterns = [
    path("sv_evaluation/", TemplateView.as_view(template_name="help/sv_evaluation.html"), name="sv_evaluation"),
    path("plots/", TemplateView.as_view(template_name="help/plots.html"), name="plots"),
    path("datasources/", TemplateView.as_view(template_name="help/datasources.html"), name="datasources"),
    path("genome_browser/", TemplateView.as_view(template_name="help/genome_browser.html"), name="genome_browser"),
    path("ontologies/", TemplateView.as_view(template_name="help/ontologies.html"), name="ontologies"),
    path("about/", TemplateView.as_view(template_name="help/about.html"), name="about"),
]
