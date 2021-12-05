library("biomaRt")

grch37 = useMart(biomart="ENSEMBL_MART_ENSEMBL", host="grch37.ensembl.org", path="/biomart/martservice", dataset="hsapiens_gene_ensembl")
attributes = c("chromosome_name", "start_position", "end_position","strand", "ensembl_gene_id", "hgnc_symbol", "entrezgene_id", "gene_biotype")

results = getBM(attributes = attributes,  mart = grch37, useCache = FALSE)

write.table(results, file = 'biomart_genes_hg19_20211204.txt', quote = FALSE, sep = "\t",  row.names = FALSE, na = "")
