library("biomaRt")

#grch38 = useMart(biomart="ENSEMBL_MART_ENSEMBL", host="grch38.ensembl.org", path="/biomart/martservice", dataset="hsapiens_gene_ensembl")
grch38 = useMart("ensembl", dataset="hsapiens_gene_ensembl")
attributes = c("chromosome_name", "start_position", "end_position","strand", "ensembl_gene_id", "hgnc_symbol", "entrezgene_id", "gene_biotype")

results = getBM(attributes = attributes,  mart = grch38, useCache = FALSE)

write.table(results, file = 'biomart_genes_hg38_20211207.txt', quote = FALSE, sep = "\t",  row.names = FALSE, na = "")
