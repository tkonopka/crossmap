# crossprep

Crossprep is a suite of scripts that parse raw data files and prepare the contents into a format that can be loaded into a crossmap instance.

The suite contains several components. 

 - [pubmed](#pubmed)
 - [genesets](#genesets)
 - [orphanet](#orphanet)
 
Each component is launched with a common syntax,

```python
python3 crossprep.py COMPONENT [...]
``` 

Here, `COMPONENT` is one of the components listed and `[...]` are arguments that pertain to that component.


## `pubmed` 

`crossprep pubmed` is a command-line utility for downloading and processing pubmed article data.

There are two main utilities accessible through the pubmedgraph.py
interface.

The first utility downloads 'baseline' article data. An example call to this utility is as follows:

```
python3 crossprep.py baseline --outdir /output/dir
```

This create an output directory and a subdirectory `baseline`, then attempts to download all baseline files from the NCBI servers. It is possible to restrict the downloads via file indexes, e.g.  

```
python3 crossprep.py baseline --outdir /output/dir --indexes 1-10
```


The second utility scans the baseline files and builds yaml datasets.

```
python3 crossprep.py pubmed--outdir /output/dir --name pubmed-all 
```

It is possible to tune the output dataset using year ranges, pattern matches, and size threholds, e.g.

```
python3 crossprep.py pubmed --outdir /output/dir --name pubmed-recent-human
         --year 2010-2019 --pattern humam --length 500
``` 

This will create a dataset holding articles from the years 2010-2019, containing the text pattern 'human' and containing at least 500 characters in the title and abstract fields. 


## `genesets`

The `genesets` utility converts sets of genes in [gmt format](http://software.broadinstitute.org/cancer/software/gsea/wiki/index.php/Data_formats#GMT:_Gene_Matrix_Transposed_file_format_.28.2A.gmt.29) - a format that uses text files to define one gene set per line - into a dataset for crossmap. The utility performs some filtering by default

```
python crossprep.py genesets --outdir /output/dir --name geneset
                             --gmt path-to-gmt.gmt.gz 
                             --gmt_min_size 5 --gmt_max_size 100
```

This will read gene sets specified on the second line and create a dataset `geneset.yaml.gz`. The ouput will contain genesets of size in the range given by `--gmt_min_size` and `--gmt_max_size`.


## `orphanet`

The `orphanet` utility uses bulk downloads from [ORPHANET](http://www.orphadata.org/). 

```
python crossprep.py orphanet --outdir /output/dir --name orphanet
                             --orphanet_phenotypes en_product4_HPO.xml
                             --orphanet_genes en_product6.xml
```

The utility assumes the xml files follow a schema concordant with orphanet bulk downloads.


