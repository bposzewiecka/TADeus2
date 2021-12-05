from django.urls import include, path
from rest_framework import routers
from ontologies.api import views

router = routers.DefaultRouter()
router.register(r'genes', views.GeneViewSet)
router.register(r'phenotypes', views.PhenotypeViewSet)

urlpatterns = [
	path('', include(router.urls)),
]
