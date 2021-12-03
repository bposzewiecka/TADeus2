# TADeus - a tool for clinical interpretation of structural variants modifying chromatin organization

TADeus is an easy-to-use open-source web application dedicated for clinical evaluation of variants in genes whose expression may be affected by chromosomal rearrangements. The main functionality of TADeus provides a view of regulatory landscape of regions surrounding breakpoints of the rearrangements by combing chromatin interaction data \textcolor{red}{(Hi-C)} with other omics data from different sources. TADeus prioritizes genes using haploinsufficiency score, number of interrupted enhancer-promoter interactions, the distance from the breakpoints, and the phenotypic data.

In addition, TADeus can serve as a genomic browser that shows Hi-C matrices with one-dimensional genomic data and allows users to compare Hi-C data from different tissues. 

# Installation

```
python3 -m venv tadeus_venv
source tadeus_venv/bin/activate
git clone https://github.com/bposzewiecka/TADeus2.git
pip install -r requirements.txt
```

## Web server implementation

TADeus is freely available at [http://bioputer.mimuw.edu.pl/tadeus](http://bioputer.mimuw.edu.pl/tadeus) and is intended to be systematically maintained. Registration is needed to exploit its full functionality. TADeus is implemented as a Python/Django web application using MySQL database as data storage. The source code of this application is deposited on Github [https://github.com/bposzewiecka/TADeus](https://github.com/bposzewiecka/TADeus). Fragments of code from HiCExplorer ([Ramirez et al.](https://www.nature.com/articles/s41467-017-02525-w)) are reused in the track plot module. TADeus contains information on the datasources used and links to websites from they were obtained: [http://bioputer.mimuw.edu.pl:82/datasources/](http://bioputer.mimuw.edu.pl:82/datasources/).
