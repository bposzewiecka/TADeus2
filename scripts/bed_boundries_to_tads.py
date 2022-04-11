import sys
from collections import defaultdict

chroms = defaultdict(list)

with open(sys.argv[1]) as f_in, open(sys.argv[2], "w") as f_out:

    for line in f_in:

        line = line.split()
        chrom = line[0]
        start = int(line[1])
        end = int(line[2])

        if line[3] != "Weak":
            chroms[chrom].append((start, end))

    for chrom, coords in chroms.items():
        coords.sort()
        last_end = 0

        for start, end in coords:
            f_out.write(f"{chrom}\t{last_end}\t{start}\n")

            last_end = end
