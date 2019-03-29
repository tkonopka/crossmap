# crossprep



## pubmed

`crossprep-pubmed` is a command-line utility for downloading and processing pubmed article data.

There are two main utilities accessible through the pubmedgraph.py
interface.

The first utility downloads 'baseline' article data. An example call to this utility is as follows:

```
python3 crossprep-pubmed.py download --outdir /output/dir
```

This create an output directory and a subdirectory `baseline`, then attempts to download all baseline files from the NCBI servers. It is possible to restrict the downloads via file indexes, e.g.  

```
python3 crossprep-pubmed.py download --outdir /output/dir --indexes 1-10
```


The second utility scans the baseline files and builds yaml datasets.

```
python3 crossprep-pubmed.py build --outdir /output/dir --name pubmed-all 
```

It is possible to tune the output dataset using year ranges, pattern matches, and size threholds, e.g.

```
python3 crossprep-pubmed.py build --outdir /output/dir --name pubmed-recent-human
         --year 2010-2019 --pattern humam --length 500
``` 

This will create a dataset holding articles from the years 2010-2019, containing the text pattern 'human' and containing at least 500 characters in the title and abstract fields. 



## obo

