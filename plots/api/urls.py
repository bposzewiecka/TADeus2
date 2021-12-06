from django.urls import include, path
from rest_framework import routers

from plots.api import views

router = routers.DefaultRouter()
router.register(r"plots", views.PlotViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
