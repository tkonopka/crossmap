Building datasets from other format
===================================

Crossprep is a suite of scripts that parse raw data files and prepare the
contents into a format that can be loaded into a crossmap instance.

The suite contains several components. 

 - [obo](#obo)
 - [pubmed](#pubmed)
 - [genesets](#genesets)
 - [orphanet](#orphanet)
 - [wiktionary](#wiktionary)
 
Each component is launched with a common syntax,

.. code:: bash

    python crossprep.py COMPONENT [...]


Here, `COMPONENT` is one of the components listed and `[...]` are arguments
that pertain to that component.



obo
~~~

`crossprep obo` is a utility for parsing ontology definition files in `obo`
format and preparing their contents for loading into a crossmap build.

Ontology files must be downloaded separately, for example from the [obo foundry](http://www.obofoundry.org/). The utility can then process the local file,

.. code:: bash

    python crossprep.py obo --obo file.obo --name obo


There are two optional settings that tune the output. One of these,
`---obo_root`, sets the root node for the output dataset. By default, the
utility processes the whole ontology hierarchy, but this setting can create
a dataset focused on any sub-branch.

.. code:: bash

    python crossprep.py obo --obo file.obo --name obo \
                        --obo_root NODE:00001

Another setting, `--obo_aux`, determines what kind of information is
transferred from the ontology definition into the output dataset. The
allowed values are `parents`, `ancestors`, `children`, `siblings`, or
combinations thereof. By default, the utility will incorporate data about
a node's parent within the definition of that node. As an example, to
incorporate information about parents and siblings, the command would be
as follows

.. code:: bash

    python crossprep.py obo --obo file.obo --name obo_parents_siblings \
                        --obo_aux parents,siblings


Pubmed abstracts
~~~~~~~~~~~~~~~~


`crossprep pubmed_baseline` is a utility for downloading article data from
 [pubmed](https://www.nlm.nih.gov/databases/download/pubmed_medline.html), and `crossprep pubmed` is an associated utility for processing that
  data.

The first utility downloads 'baseline' article data. An example call to this
 utility is as follows:

.. code:: bash

    python crossprep.py pubmed_baseline --outdir /output/dir


This create an output directory and a subdirectory `baseline`, then attempts
to download all baseline files from the NCBI servers. It is possible to
restrict the downloads via file indexes, e.g.

.. code:: bash

    python crossprep.py baseline --outdir /output/dir --baseline_indexes 1-10



The `crossprep pubmed` utility scans the downloaded baseline files and builds
yaml datasets.

.. code:: bash

    python crossprep.py pubmed --outdir /output/dir --name pubmed-all


It is possible to tune the output dataset using year ranges, pattern matches,
and size thresholds, e.g.

.. code:: bash

    python crossprep.py pubmed --outdir /output/dir --name pubmed-recent-human \
         --pubmed_year 2010-2019 --pubmed_pattern humam --pubmed_length 500


This will create a dataset holding articles from the years 2010-2019
, containing the text pattern 'human' and containing at least 500 characters
in the title and abstract fields.


Gene sets
~~~~~~~~~

The `genesets` utility converts sets of genes in [gmt format](http://software.broadinstitute.org/cancer/software/gsea/wiki/index.php/Data_formats#GMT:_Gene_Matrix_Transposed_file_format_.28.2A.gmt.29)
- a format that uses text files to define one gene set per line - into a dataset for crossmap.
The utility performs some filtering by default

.. code:: bash

    python crossprep.py genesets --outdir /output/dir --name geneset \
                             --gmt path-to-gmt.gmt.gz \
                             --gmt_min_size 5 --gmt_max_size 100


This will read gene sets specified on the second line and create a dataset
`geneset.yaml.gz`. The ouput will contain genesets of size in the range
given by `--gmt_min_size` and `--gmt_max_size`.


Orphanet diseases
~~~~~~~~~~~~~~~~~

[Orphanet](http://www.orphadata.org/) is a curated knowledge-base on diseases
, including their phenotypes and associated genetic causes. Parts of their
database are available for download as xml files. The `orphanet` utility can
parse these files and prepare summaries suitable for `crossmap`.

.. code:: bash

    python crossprep.py orphanet --outdir /output/dir --name orphanet \
                             --orphanet_phenotypes en_product4_HPO.xml \
                             --orphanet_genes en_product6.xml




Wiktionary
~~~~~~~~~~

[Wiktionary](http://www.wiktionary.org) is an online dictionary that is part
of [wikimedia](http://www.wikimedia.org). It provides bulk downloads of all
the word definitions in its database. The `wiktionary` utility parses the
definitions and constructs files that are suitable for `crossmap`.

.. code:: bash

    python crossprep.py wiktionary --outdir /output/dir --name wiktionary \
                       --wiktionary enwiktionary-pages-articles.xml.bz2 \
                       --wiktionary_length 10


This command taks as input `xml.bz2` compressed files, as provided by the
wiktionary download page. The second argument is numerical factor that
instructs the utility to skip over some words and the definitions. The
utility looks at the length (number of characters) of words and their
definitions. If the ratio of lengths for the definition and the word is
smaller than the threshold, the word is omitted from the ouput.

 