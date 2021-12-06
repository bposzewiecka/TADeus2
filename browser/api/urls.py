from django.urls import include, path
from rest_framework import routers

from browser.api import views

router = routers.DefaultRouter()
router.register(r"breakpoints", views.BrowserViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
