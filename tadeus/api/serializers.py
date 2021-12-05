from rest_framework import serializers

from tadeus.models import Assembly, Chromosome, Plot, Sample, Species, TrackFile


class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = ["id", "name"]


class ChromosomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chromosome
        fields = ["id", "name", "size"]


class AssemblySerializer(serializers.ModelSerializer):
    chromosomes = ChromosomeSerializer(many=True)
    species = SpeciesSerializer(many=False)

    class Meta:
        model = Assembly
        fields = ["id", "name", "species", "chromosomes"]


class AssemblyShortSerializer(serializers.ModelSerializer):
    species = SpeciesSerializer(many=False)

    class Meta:
        model = Assembly
        fields = ["id", "name", "species"]


class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = ["id", "name", "tissue", "description", "species"]


class PlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plot
        fields = ["id", "assembly", "name", "title", "public"]


class TrackFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackFile
        fields = ["id", "assembly", "sample", "name", "file_type", "bed_sub_type", "source_name", "source_url", "reference", "public"]
