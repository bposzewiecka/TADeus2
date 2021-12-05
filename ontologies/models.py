from django.db import models
from django.utils.html import format_html

from datasources.models import BedFileEntry


class Gene(BedFileEntry):
    ensembl_gene_id = models.CharField(max_length=20, null=True, blank=True)
    gene_biotype = models.CharField(max_length=20, null=True, blank=True)
    entrezgene_id = models.CharField(max_length=20, null=True, blank=True)


class Phenotype(models.Model):
    db = models.CharField(max_length=10)
    pheno_id = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    definition = models.CharField(max_length=1000, null=True)
    comment = models.CharField(max_length=2000, null=True)
    is_a = models.ManyToManyField("self", symmetrical=False)
    genes = models.ManyToManyField(Gene, related_name="phenotypes", through="GeneToPhenotype")

    def __str__(self):
        return self.pheno_id

    @property
    def url(self):
        url = None

        if self.db == "HPO":
            url = f"http://compbio.charite.de/hpoweb/showterm?id={self.pheno_id}"

        if self.db == "OMIM":
            url = f"https://www.omim.org/entry/{self.pheno_id}"

        if self.db == "ORPHA":
            url = "https://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=EN&Expert={pheno_id}".format(pheno_id=self.pheno_id.split(":")[1])

        return url

    @property
    def link(self):

        link = self.url

        if self.db == "HPO":

            return format_html('<a href="{link}" target="_blank">{name}</a>', link=link, name=self.pheno_id)

        if self.db == "OMIM":
            return format_html('<a href="{link}" target="_blank">OMIM:{name}</a>', link=link, name=self.pheno_id)

        if self.db == "ORPHA":
            return format_html('<a href="{link}" target="_blank">{name}</a>', link=link, name=self.pheno_id)

        return None


class GeneToPhenotype(models.Model):
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    phenotype = models.ForeignKey(Phenotype, on_delete=models.CASCADE)
    frequent = models.BooleanField(default=False)

    class Meta:
        ordering = [
            "gene",
        ]
