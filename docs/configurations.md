# crossmap configuration

Each crossmap instance is configured via a yaml file. The settings determine how data are stored internally. Many of the settings affect the build stage and it is important that they remain unchanged at all subsequent stages. 


## Representative configuration
 
A representative configuration might be as follows: 

```yaml
name: crossmap-name
comment: short comment
data:
  primary: path-to-primary.yaml.gz
  secondary: path-to-secondary.yaml.gz
tokens:
  k: 6
features:
  max_number: 20000
  weighting: [0, 1]
```

Among the key-value pairs in this example, only *name* and *data" are required. The other fields fine-tune how data is stored in the back-end. While those fields are not strictly required - crossmap can fill in default values - it is nonethless informative to include them to summarize how the data is represented in the back-end. 


## Complete configuration

Some settings are specified at the root level of the configuration yaml file, while others are grouped into sublevels.

Core settings are present at the root level of the configuration yaml file. 

 - *name* - string distinguishing one crossmap instance from another. Used as the directory name where instance files are stored.
 - *comment* - string. Used only for human readability of the configuration file to give the purpose of the instance.
 
Other settings are organized into subgroups.  
 

 ### `data` 
 
The purpose of the `data` subgroup is to specify the locations of data to be included in the crossmap database. The configuration also specified names, or labels, for each of the datasets.

Example:

```yaml
data:
  primary: path-to-primary.yaml.gz
  secondary: path-to-secondary.yaml.gz
``` 

In this example, the labels *primary* and *secondary* are not keywords, but rather user-specified labels. Thus, it is possible to use labels 'A' and 'B' instead, or any other label that is compatible with yaml.
 
 
 
 ### `tokens` 
 
 Settings in the 'tokens' determine how raw data are partitioned into smaller components. The algorithm essentially splits text into k-mers.
 
  - *k* - integer, length of kmers
  - *alphabet* - string without spaces. Used to specify the characters that are allowed to exist in tokens. Other characters are removed. Defaults to alphanumeric characters.
 
Example:
 
 ```yaml
tokens:
  k: 6
  alphabet: ABCDEFGHIJKLMNOPQRSTUVWXYZ
```
 

### `features`  

Settings in the `features` subgroup control how tokens parsed out of the raw data are used to build a representation of the original data. Roughly, each token type can constitute one feature in the data model, but there is some control about the weighting of the features and other aspects of the ensembl of features.

 - *max_number* - integer. The total number of features is estimated from the contents of the data files. The number of features, however, is capped at this threshold. Defaults to 0, interpreted as an unlimited number of features.
 - *min_count* - integer. Used to discard some features observed in very few data items. Defaults to 0. 
 - *weighting* - array of two numbers, `[a, b]`. Used to determine the weight of each feature with a linear formula, `weight = a + b * IC`, where `IC` is the information content of the feature (logarithm of inverse frequency in the datasets). The weighting array defaults to [0, 1].
 - *map* - path to a file with a tab-separated table of features and weights. When specified, the features listed in the file are used as-is. This settings overrides de-novo feature discovery and overrides other settings in this group. Defaults to None/null, which indicates that features should be extracted and weighted using the datasets in the `data` group.


Example (for identifying search from data files)

```yaml
features:
  max_number: 20000
  min_count: 2
  weighting: [0, 1]
```

Example (for using pre-specified features)

```yaml
features:
  map: path-to-features.tsv.gz

```

### `cache`

The `cache` settings are not used during the build stage, but rather affect runtime during subsequent stages (prediction, decomposition, server mode). The settings specify how many objects from the disk database can be cached in memory, and thus provide a means to speed up execution at the cost of increasing memory use. All the items in this group are integers.

 - *counts* - integer, number of database rows pertaining to diffusion
 - *ids* - integer, number of integer/string mappings
 - *titles* -integer, number of item titles
 - *data* - integer, number of data items 

Example:

```yaml
cache:
  counts: 20000
  ids: 10000
  titles: 50000
  data: 20000
```


### `logging`

`logging` settings control the amount of information that is output by the crossmap at runtime. 

 - *level* - string, one of ('INFO', 'WARNING', 'ERROR'); determines standard logging level; can be over-ridden by a command line argument
 - *progress* - integer, determines interval at which progress messages are displayed during tbe build stage
 
 Example:
 
 ```yaml
 logging:
  level: INFO
  progress: 50000
```
 
  
### `server`

When crossmap is run in server mode, there are additional parameters that determine who the program communicates with the network.

 - *api_port* - integer; the network port on localhost that accepts requests
 - *ui_port* - integer; the network port on localhost that displays the graphical user interface

Example

```yaml
server:
  api_port: 8098
  ui_port: 8099
```
 
