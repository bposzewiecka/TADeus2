from django.urls import include, path
from rest_framework import routers
from tadeus.api import views

router = routers.DefaultRouter()
router.register(r'species', views.SpeciesViewSet)
router.register(r'assemblies', views.AssemblyViewSet)
router.register(r'samples', views.SampleViewSet)
router.register(r'plots', views.PlotViewSet)
router.register(r'trackFiles', views.TrackFileViewSet)

urlpatterns = [
	path('', include(router.urls)),
]
