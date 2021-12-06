from django.urls import include, path
from rest_framework import routers

from tracks.api import views

router = routers.DefaultRouter()
router.register(r"tracks", views.TrackViewSet)
router.register(r"tracks_parameters_options", views.TrackParametersOptionsViewSet, basename="track_parameters_options")

urlpatterns = [
    path("", include(router.urls)),
]
