from rest_framework import serializers

from plots.models import Plot


class PlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plot
        fields = ["id", "assembly", "name", "title", "public"]
