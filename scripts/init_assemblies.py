from datasources.models import Species, Assembly, Chromosome

def init_species(name):

    q = Species(name=name)
    q.save()
    return q

def init_assembly(name, species, chrom_sizes_fn):

    assembly = Assembly(species = species, name =  name)
    assembly.save()
   
    with open(chrom_sizes_fn) as f:

        for line in f:
            line = line.split()
            chrom = Chromosome(assembly = assembly, name = line[0], size = int(line[1]))
            chrom.save()

def init_human_assemblies():

    Chromosome.objects.all().delete()
    Assembly.objects.all().delete()
    Species.objects.all().delete()

    human = init_species('Human')
    init_assembly('hg19', human, 'data/hg19/hg19_chrom_sizes.txt')
    init_assembly('hg38', human, 'data/hg38/hg38_chrom_sizes.txt')

globals().update(locals())

init_human_assemblies()