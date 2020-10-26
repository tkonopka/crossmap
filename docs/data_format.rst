Data format
===========

Data files must be prepared in yaml format. Given that ``crossmap`` is meant
for integration of many different types of data, it may seem ironic that the
software only accepts one data format. However, this data format is actually
quite accommodating and content from other file formats can be transferred
into yaml.


Primary data
~~~~~~~~~~~~

Yaml files are expected to be lists mapping item identifiers to associated
data. As an example, assuming we have two data items with identifiers
``item:1`` and ``item:2``, a dataset file might look as follows:

.. code:: yaml

    item:1:
      data: content for item 1
    item:2:
      data: content for item 2

The keywords ``data`` instructs crossmap to convert those strings into
the primary data associated with the item identifiers. Thus, after loading
these items into a crossmap instance, it will be possible to retrieve the
items via queries such as 'item', 'content', or the numbers '1' and '2'.


Metadata
~~~~~~~~

Each item can be associated with metadata field. The content of this field
is recorded in the crossmap database but is not used for any calculations.
The field can serve to enhance readability, or for secondary analysis.

Examples:

.. code:: yaml

    item:3:
      data: A B C
      metadata:
        id: item:3
        source: item source
    item:4:
      data: D E F
      metadata: description for item 4

There are no constraints on the form or the content of metadata. One of the
examples above, for example, uses a dictionary to organize information into
key/value pairs.


Structured and nested data
~~~~~~~~~~~~~~~~~~~~~~~~~~

The content of the ``data`` field can be structured as arbitrary objects.
In particular, dictionaries of key/value pairs and arrays are valid.

Examples:

.. code:: yaml

    item:nested:
      data:
        key1: value1
        key2: value2
        key3:
          key4: value4
    item:array:
      data: [value1, value2]

It is important that when ``data`` is a dictionary, its keys are not
transferred into the object representations. Thus, searching the above data
collection for the string 'key1' would not produce a hit. However, nested
objects are stringified and their keys can become part of the object
representations. Thus, searching for 'key4' would match ``item:nested``.


Weighting of text-based data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Text under the ``data`` fields is split into k-mers, and each k-mer is
weighted according to a strategy determined during the instance build process.
However, there is some flexibility to increase or decrease the weight
associated with certain features / k-mers. Weights can be increased
through repetition. Negative weights can be assigned through a ``data_neg``
field.

Examples:

.. code:: yaml

    item:single:
      data: A B
    item:increase:
      data: A B B B
    item:negative:
      data_pos: A
      data_neg: B

In these examples, the numeric representation of ``item:repeated`` will be
skewed in favor of feature ``B`` compared to the representation of
``item:single``. The numeric representation of ``item:negative`` will include
a negative value for feature ``B``.


Numeric weighting
~~~~~~~~~~~~~~~~~

To achieve more control over the feature weighting, items
can be specified through a field ``value`` instead of ``data``.

Examples:

.. code:: yaml

    item:equal:
      value:
        A: 1.0
        B: 1.0
    item:skewed:
      value:
        A: 1.0
        B: 2.5
    item:biased:
      data: A B
      value:
        X: 2.0

Specifying values for each feature gives full control over the relative
weighting between features.

Note that whereas text under ``data`` is parsed automatically into k-mers
and then used to to construct a numeric representation, features
under ``value`` are used as-is.

Note that the ``data`` and ``value`` fields can be specified together.
``crossmap`` will then use both fields to construct a joint numeric
representation of the items. This representation will arise from a
deterministic procedure, but the relative weighting of the various
features will not be obvious from the data file alone.

