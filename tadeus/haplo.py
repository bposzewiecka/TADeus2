"""
def main():

    import random
    from functools import reduce

    import matplotlib.pyplot as plt
    import numpy as np

    from tadeus.models import Assembly, TrackFile

    haploins_pred = TrackFile.objects.get(pk=5)

    def haplo_prob(chrom, start, end):

        genes = haploins_pred.get_entries(chrom=chrom, start=start, end=end)

        scores = [1 - gene.score for gene in genes]
        log_scores = [np.log10(1 - gene.score) for gene in genes]

        # prob = reduce(lambda a,b:  a * b, scores, 1)

        log_prob = reduce(lambda a, b: a + b, log_scores, 0)
        # 	print(log_scores)

        return log_prob

    def perm(bed_entry, numb):

        chrom = bed_entry.chrom
        start = bed_entry.start
        end = bed_entry.end

        size = end - start

        hg19 = Assembly.objects.get(name="hg19")
        chromosomes = hg19.chromosomes.exclude(name="chrY")

        scores = []

        i = 1

        while i < 1000:
            rand_chrom = random.sample(list(chromosomes), 1)[0]
            rand_chrom_len = rand_chrom.size

            if rand_chrom_len - size < size:
                continue

            rand_chrom_name = rand_chrom.name
            rand_start = random.randint(1, rand_chrom_len - size)
            rand_end = rand_start + size

            hs = haplo_prob(rand_chromhrom_name, rand_start, rand_end)

            if hs == 0:
                continue
            # 			print(hs)

            if not np.isnan(hs):
                scores.append(hs)

            i += 1

        # 		print(scores)
        plt.hist(scores, 50)
        plt.title(f"Histogram {bed_entry} - size {size:,} ")

        plt.axvline(x=haplo_prob(chrom, start, end))
        plt.savefig("/home/basia/CNVBrowser/data/human/output/without_one/fig_" + str(numb).zfill(2) + ".png")
        plt.close()

    def ibn():

        ibn_salem = TrackFile.objects.get(pk=14)
        haploins_pred = TrackFile.objects.get(pk=5)

        cnvs = list(ibn_salem.file_entries.all())

        cnvs.sort(key=lambda x: x.end - x.start)

        for idx, cnv in enumerate(cnvs):
            chrom = cnv.chrom
            start = cnv.start
            end = cnv.end
            perm(cnv, idx)

    def haplo_dels(pk, file):

        dels = TrackFile.objects.get(pk=pk)
        haploins_pred = TrackFile.objects.get(pk=5)

        scores = []
        for cnv in dels.file_entries.all():
            # if  len(cnv) < 100000 or len(cnv) > 400000:
            # 		continue
            score = haplo_prob(cnv.chrom, cnv.start, cnv.end)
            if np.isnan(score):
                continue

            print(score)
            scores.append(score)

        plt.hist(scores, 50)

        plt.savefig(file)
        plt.close()

    tads = TrackFile.objects.get(pk=6)

    def haplo_dels_intersect(pk, file):

        dels = TrackFile.objects.get(pk=pk)

        l = []
        for cnv in dels.file_entries.all():
            # if  len(cnv) < 100000 or len(cnv) > 400000:
            # 	continue
            t = tads.get_entries(cnv.chrom, cnv.start, cnv.end)
            l.append(len(t))

        plt.hist(l)

        plt.savefig(file)
        plt.close()

    def dels_hist(pk, file):

        track_file = TrackFile.objects.get(pk=pk)

        entry_len = [np.log10(entry.end - entry.start) for entry in track_file.file_entries.all()]  # if len(entry) > 100000 and len(entry) < 400000

        plt.hist(entry_len, 50)
        plt.savefig(file)
        plt.close()

    def aaa():
        def bbb(entries, pathogenic):
            for entry in entries:

                haplo = haplo_prob(entry.chrom, entry.start, entry.end)
                num_of_tads = len(tads.get_entries(entry.chrom, entry.start, entry.end))

                print("\t".join([pathogenic, entry.chrom, str(entry.start), str(entry.end), str(haplo), str(num_of_tads)]))

        genomes1000 = TrackFile.objects.get(pk=7).file_entries.all()
        clinvar = TrackFile.objects.get(pk=15).file_entries.all()

        bbb(genomes1000, "No")
        bbb(clinvar, "Yes")

    aaa()
    # dels_hist(7, '/home/basia/CNVBrowser/data/human/output/hist_1000genomes.png')


# 	dels_hist(15, '/home/basia/CNVBrowser/data/human/output/hist_clinvar.png')

# 	haplo_dels(7, '/home/basia/CNVBrowser/data/human/output/haploin_1000genomes.png')
# 	haplo_dels(15, '/home/basia/CNVBrowser/data/human/output/haploin_clinvar.png')

# 	haplo_dels_intersect(7, '/home/basia/CNVBrowser/data/human/output/inter_1000genomes.png')
# 	haplo_dels_intersect(15, '/home/basia/CNVBrowser/data/human/output/inter_clinvar.png')


main()
"""
