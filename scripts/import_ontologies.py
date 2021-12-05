import csv
from collections import Counter
from ontologies.models import  Phenotype, GeneToPhenotype, Gene
from datasources.models import Assembly, TrackFile
from django.contrib.auth.models import User
from django.db import transaction

def del_all():
    Phenotype.objects.all().delete()
    Gene.objects.all().delete()

@transaction.atomic
def get_genes():

    hg19 = Assembly.objects.get(name = 'hg19')
    admin = User.objects.get(username = 'admin')

    file_name = 'data/ontologies/GENES/biomart_genes_hg19_20211204.txt'

    trackFile = TrackFile(id = 2, assembly = hg19,
        name = '',
        source_name='',
        source_url = '',
        file_type = 'BE', bed_sub_type = 'Bed6', owner = admin, public = True, approved = True)

    trackFile.save()

    with open(file_name, 'r') as csvfile:
        
        reader = csv.DictReader(csvfile, delimiter='\t')

        for row in reader:
        
            name =  row['hgnc_symbol'].upper()
            ensembl_gene_id = row['ensembl_gene_id'] if row['ensembl_gene_id'] else None
            gene_biotype = row['gene_biotype']
            entrezgene_id =  row['entrezgene_id'] if row['entrezgene_id'] else None

            chrom =  row['chromosome_name']
            start = row['start_position']
            end = row['end_position']
            strand = '+' if row['strand'] == '1' else '-'

            if chrom.startswith('G') or chrom.startswith('H'):
                continue

            chrom = 'chr' + row['chromosome_name']

            gene = Gene(name = name,   
                chrom = chrom,
                start = start,
                end = end,
                strand = strand,
                gene_biotype = gene_biotype,
                ensembl_gene_id = ensembl_gene_id,
                entrezgene_id = entrezgene_id,
                track_file =  trackFile)
            gene.save()


@transaction.atomic
def get_hpo_terms():

    file_name = 'data/ontologies/HPO/hp.obo'

    hpo_terms = { }

    with open(file_name, 'r') as f:

        for line in f:
            if line == '\n':
                break

        for line in f:

            # omiting header
            if line == '[Term]\n':
                data = {}
                continue

            if line == '\n':
                pheno_id = data['id'][0]
                name = data['name'][0]
                definition = data.get('def', [None])[0]
                comment = data.get('comment', [None])[0]

                if 'is_a' in data:
                    is_a = [  i.split()[0] for i in data['is_a']]
                    data['is_a'] = is_a

                phenotype = Phenotype(db = 'HPO', pheno_id = pheno_id, name = name, definition = definition, comment = comment)
                phenotype.save()
                hpo_terms[pheno_id] = (phenotype, data)

                continue

            ic = line.find(':')
            name = line[:ic]
            rest = line[ic+1:].strip()

            name_data = data.get(name, [])
            name_data.append(rest)
            data[name] = name_data

    for pheno_id, (hpo_term, data) in hpo_terms.items():
        if 'is_a' in data:
            is_a = data['is_a']

            parents = [ hpo_terms[parent_pheno_id][0] for parent_pheno_id in is_a]

            hpo_term.is_a.add(*parents)
            hpo_term.save()

def get_phenotypes(db):
    return { phenotype.pheno_id: phenotype for phenotype in Phenotype.objects.filter(db=db)}


def get_hpo_terms_genes():

    file_name = 'data/ontologies/HPO/genes_to_phenotype.txt'

    phenotypes = get_phenotypes('HPO')

    with open(file_name, 'r') as f:
    
        a = set()
        
        reader = csv.DictReader(f, delimiter='\t')

        for row in reader: 

            entrezgene_id = row['entrez-gene-id']
            pheno_id = row['HPO-Term-ID']

            genes = Gene.objects.all().filter(entrezgene_id=entrezgene_id)
            phenotype = phenotypes[pheno_id]

            for gene in genes:   
                g2p = GeneToPhenotype(gene = gene, phenotype=phenotype)
                g2p.save()

                if len(genes) == 0:
                    a.add((row['entrez-gene-symbol']))

        print(a, len(a))

@transaction.atomic
def get_omim_phenotypes():

    file_name = 'data/ontologies/omim/mimTitles.txt'          

    with open(file_name, 'r') as f:


        for line in f:
            line = line.strip().split('\t')

            if line[0][0] == '#': continue

            if line[0] in ('Asterisk'): continue

            phenotype = Phenotype(db = 'OMIM', pheno_id = int(line[1]), name=line[2], comment = line[0])
            phenotype.save()

@transaction.atomic
def get_omim_phenotypes_to_genes():

    file_name = 'data/ontologies/hpo/diseases_to_genes.txt'

    with open(file_name, 'r') as f:
        
        f.readline()

        phenotypes = Phenotype.objects.filter(db = 'OMIM')
        phenotypes = { phenotype.pheno_id : phenotype for phenotype in phenotypes}

        genes = get_genes_names()
        gene_ensembl_ids =  get_genes_ensembl_ids()

        phenotypes_to_genes = []

        genes_aliases  = get_genes_aliases()

        bad_genes =set()

        for line in f:

            row    = line.strip().split('\t')

            if row[0].startswith('ORPHA'): continue

            pheno_id = row[0].split(':')[1]

            if len(row) == 3:

                gene_symbol = row[2]

                gene = None

                if gene_symbol in genes:
                    gene = genes[gene_symbol]
                elif gene in  genes_aliases:
                    ensembl_gene_id  = genes_aliases[gene_symbol]
                    gene = gene_ensembl_ids.get(ensembl_gene_id, None)

                if gene:
                    phenotype =  phenotypes[pheno_id]
                    g2p = GeneToPhenotype(gene = gene, phenotype=phenotype)
                    g2p.save()
                else:
                    bad_genes.add(gene_symbol)

    for gene in sorted(bad_genes):
        print(gene)

globals().update(locals())

del_all()
get_genes()
#print('get_genes')
get_hpo_terms()
#print('get_hpo_terms')
get_hpo_terms_genes()
#print('get_hpo_terms_genes')
#get_omim_phenotypes()
#print('get_omim_phenotypes')
#get_omim_phenotypes_to_genes()
#print('get_omim_phenotypes_to_genes')