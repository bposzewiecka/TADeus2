from rest_framework import viewsets
from rest_framework.response import Response


class EvaluationPvalueViewSet(viewsets.ViewSet):
    def list(self, request, format=None):

        content = {
            "chrom": "",
            "coordinate": "",
            "p-value": "",
            "assembly": "",
        }

        return Response(content)
