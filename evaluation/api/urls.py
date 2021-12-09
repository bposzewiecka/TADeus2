from django.urls import include, path
from rest_framework import routers

from evaluation.api import views

router = routers.DefaultRouter()

router.register(r"evaluate_pvalue", views.EvaluationPvalueViewSet, basename="evaluate_pvalue")
router.register(r"evaluate_gene_ranking", views.EvaluationPvalueViewSet, basename="evaluate_gene_ranking")
router.register(r"evaluate_image", views.EvaluationPvalueViewSet, basename="evaluate_image")
router.register(r"evaluate_all", views.EvaluationPvalueViewSet, basename="evaluate_all")
router.register(r"evaluations", views.EvaluationPvalueViewSet, basename="evaluations")

urlpatterns = [
    path("", include(router.urls)),
]
