Data conversion from other formats
==================================

crossmap requires input in a specific format. At the same time, it is meant
to integrate many types of data. To reconcile these two factors, the
repository provides a suite of scripts to convert data in existing formats
into a form that can be loaded into crossmap instances.

The suite is implemented as module ``crossprep.py``, which is located in directory
``crossprep``. This is a script that can be executed with the following pattern.

.. code:: bash

    python crossprep.py COMPONENT [...]

Here, ``COMPONENT`` is a type of dataset to prepare and  ``[...]`` are arguments
that pertain to that component.


Ontology definitions
~~~~~~~~~~~~~~~~~~~~

Ontologies store concept definitions that are relevant to a domain, along with
relations between them. A common file format to encode ontology data is 'obo'.
``crossprep obo`` is a utility for parsing 'obo' files and preparing their
contents for loading into a crossmap instance.

Ontology files must be downloaded separately, for example from the
`OBO Foundry <http://www.obofoundry.org/>`__. The utility can then process the
local file,

.. code:: bash

    python crossprep.py obo --obo file.obo --name obo


Optional settings can tune the data transferred from the 'obo' file to
the crossmap data file. One of these, ``--obo_root``, sets the root node
for the output dataset. By default, the utility processes the whole
ontology hierarchy. The ``--obo_root`` argument can instead create a dataset
for a particular branch of the ontology.

.. code:: bash

    python crossprep.py obo --obo file.obo --name obo \
                        --obo_root NODE:00001

Another setting, `--obo_aux`, determines what kind of information is
transferred from the ontology definition into the output dataset. The
allowed values are `parents`, `ancestors`, `children`, `siblings`, or
combinations thereof (separated by commas). By default, the utility
incorporates data about a node's parent within the definition of that
node. As an example, to incorporate information about parents and siblings,
the command would be:

.. code:: bash

    python crossprep.py obo --obo file.obo \
                        --name obo_parents_siblings \
                        --obo_aux parents,siblings


Pubmed abstracts
~~~~~~~~~~~~~~~~

`Pubmed <https://pubmed.ncbi.nlm.nih.gov/>`_ is an
`NCBI <https://www.ncbi.nlm.nih.gov/>`_ service that indexes scientific
articles published in the life sciences.

``crossprep pubmed_baseline`` is a utility for downloading article data from
`pubmed <https://www.nlm.nih.gov/databases/download/pubmed_medline.html>`__,
and ``crossprep pubmed`` is an associated utility for processing that data.

The first utility downloads baseline article data. An example call to this
utility is as follows:

.. code:: bash

    python crossprep.py pubmed_baseline --outdir /output/dir

This creates an output directory and a subdirectory ``baseline``, then attempts
to download all baseline files from the NCBI servers. It is possible to
restrict the downloads via file indexes, e.g.

.. code:: bash

    python crossprep.py baseline --outdir /output/dir \
                        --baseline_indexes 1-10

The `crossprep pubmed` utility scans the downloaded baseline files and builds
yaml datasets.

.. code:: bash

    python crossprep.py pubmed --outdir /output/dir --name pubmed-all

It is possible to tune the output dataset using year ranges, pattern matches,
and size thresholds, e.g.

.. code:: bash

    python crossprep.py pubmed --outdir /output/dir \
                        --name pubmed-recent-human \
                        --pubmed_year 2010-2019 \
                        --pubmed_pattern human \
                        --pubmed_length 500

This will create a dataset holding articles from the years 2010-2019,
containing the text pattern 'human' and containing at least 500 characters
in the title and abstract fields.


Gene sets
~~~~~~~~~

There are many file formats used to convey sets of genes. One of the simplest
is the `gmt format <http://software.broadinstitute.org/cancer/software/gsea/wiki/index.php/Data_formats#GMT:_Gene_Matrix_Transposed_file_format_.28.2A.gmt.29>`__.
This stores sets 'horizontally', with each set occupying one line of text.

The `crossprep genesets` utility converts gene sets in the gmt format into
a dataset for crossmap. The utility can be used to filter gene sets by size.

.. code:: bash

    python crossprep.py genesets --outdir /output/dir \
                        --name geneset \
                        --gmt path-to-gmt.gmt.gz \
                        --gmt_min_size 5 --gmt_max_size 100

This will read gene sets specified via argument ``--gmt`` create a dataset
`geneset.yaml.gz`. The output will contain genesets of size in the range
given by `--gmt_min_size` and `--gmt_max_size`.


Orphanet diseases
~~~~~~~~~~~~~~~~~

`Orphanet <http://www.orphadata.org/>`_ is a curated knowledge-base on diseases
, including their phenotypes and associated genetic causes. Parts of their
database are available for download as xml files.

The ``orphanet`` utility parses these files and prepare diseases summaries.

.. code:: bash

    python crossprep.py orphanet --outdir /output/dir \
                        --name orphanet \
                        --orphanet_nomenclature en_product1.xml \
                        --orphanet_phenotypes en_product4.xml \
                        --orphanet_genes en_product6.xml




Wiktionary
~~~~~~~~~~

`Wiktionary <http://www.wiktionary.org>`_ is an online dictionary that is part
of `Wikimedia <http://www.wikimedia.org>`_. It provides bulk downloads of all
the word definitions in its database.

The ``wiktionary`` utility parses the word definitions and constructs data
files for crossmap.

.. code:: bash

    python crossprep.py wiktionary --outdir /output/dir \
                  --name wiktionary \
                  --wiktionary enwiktionary-pages-articles.xml.bz2 \
                  --wiktionary_length 10

This command processes compressed xml files, as provided by the
wiktionary download page. The last argument is a numerical factor that
instructs the utility to skip some words if the length of the definition
(measured in characters) is not longer than 10 times the length of the word
itself; this is a mechanism to skip stub entries in the dictionary.

