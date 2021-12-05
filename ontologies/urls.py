from django.urls import path

from . import views

app_name = "ontologies"

urlpatterns = [
    path("<p_db>", views.phenotypes, name="phenotypes"),
    path("genes/", views.genes, name="genes"),
    path("genes/<int:p_id>", views.gene, name="gene"),
]
