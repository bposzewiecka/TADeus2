"""tadeus_portal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from datasources.api.urls import router as datasources_router
from ontologies.api.urls import router as ontologies_router
from plots.api.urls import router as plots_router

urlpatterns = [
    path("", include("tadeus.urls")),
    path("tracks/", include("tracks.urls")),
    path("help/", include("help.urls")),
    path("plots/", include("plots.urls")),
    path("browser/", include("browser.urls")),
    path("ontologies/", include("ontologies.urls")),
    path("datasources/", include("datasources.urls")),
    path("evaluation/", include("evaluation.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
]

router = routers.DefaultRouter()


def add_router(subrouter):
    router.registry.extend(subrouter.registry)


add_router(plots_router)
add_router(ontologies_router)
add_router(datasources_router)

api_urlpatterns = [path("api/", include(router.urls))]

urlpatterns += api_urlpatterns
