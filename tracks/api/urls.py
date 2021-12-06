from django.urls import include, path
from rest_framework import routers

from tracks.api import views

router = routers.DefaultRouter()
router.register(r"tracks", views.GeneViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
