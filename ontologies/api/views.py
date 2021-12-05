from django.db.models import F
from rest_framework import viewsets

from ontologies.api.serializers import GeneListSerializer, GeneSerializer, PhenotypeSerializer
from ontologies.models import Gene, Phenotype


class GeneViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all().order_by(F("name").asc(nulls_last=True))
    http_method_names = ["get"]
    serializer_class = GeneListSerializer

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.serializer_action_classes = {
            "list": GeneListSerializer,
            "create": GeneSerializer,
            "retrieve": GeneSerializer,
            "update": GeneSerializer,
            "partial_update": GeneSerializer,
            "destroy": GeneSerializer,
        }

    def get_serializer_class(self, *args, **kwargs):
        """Instantiate the list of serializers per action from class attribute (must be defined)."""
        kwargs["partial"] = True
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_serializer_class()


class PhenotypeViewSet(viewsets.ModelViewSet):
    queryset = Phenotype.objects.all().order_by("name")
    serializer_class = PhenotypeSerializer
    http_method_names = ["get"]
