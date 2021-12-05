from rest_framework import serializers


from ontologies.models import Gene, Phenotype

class PhenotypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Phenotype
        fields = ['id', 'db', 'pheno_id', 'name', 'definition', 'comment', 'is_a']  

class GeneSerializer(serializers.ModelSerializer):

    phenotypes = PhenotypeSerializer(many=True)

    class Meta:
        model = Gene

        fields = ['id', 'chrom', 'start', 'end', 'name', 'ensembl_gene_id', 'entrezgene_id', 'gene_biotype', 'phenotypes']    


class GeneListSerializer(serializers.ModelSerializer):


    class Meta:
        model = Gene

        fields = ['id', 'chrom', 'start', 'end', 'name', 'ensembl_gene_id', 'entrezgene_id', 'gene_biotype']            