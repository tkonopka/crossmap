Data format
===========

Data files input to ``crossmap`` during the build stage and also during
other queries must be prepared in yaml format with particular fields.
Given that ``crossmap`` is meant for integration of many different types of
data, it may seem ironic that the software only accepts one data format.
However, this data format is actually quite accommodating.

Data files are expected to be lists mapping item identifiers to
associated data. As an example, assuming we have two data items with
identifiers ``item:1`` and ``item:2``, a minimal dataset file might look
as follows:

.. code:: yaml

    item:1:
      data: content for item 1
    item:2:
      data: content for item 2

Each item is linked to a brief description under the ``data`` field.
The keyword ``data`` instructs ``crossmap`` to convert those
strings into numerical representations.


Metadata
~~~~~~~~

Each item can be associated with a metadata field. The content of this field
is recorded in the ``crossmap`` database but is not used for any calculations.
The field thus serves to capture comments, either for human readability, or
for secondary analysis.

Examples:

.. code:: yaml

    item:3:
      data: A B C
      metadata:
        id: item:3
        source:
    item:4:
      data: D E F
      metadata: description for item 4

There are no constraints on the form or the content of metadata.


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

Specifying data as a dictionary can be particularly useful to aid
human-readability. It is important that when a ``data`` field is a dictionary,
its keys are not transferred into the object representations.
Thus, searching the above data collection for the string 'key1' would not
produce a hit. However, nested objects are stringified and thus keys in
nested objects become part of the object representations. Thus, searching for
the string 'key4' would match ''item:nested''.


Weighting of text-based data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Text under the ``data`` fields are weighted according to a centralized
k-mer-weighting strategy. However, there is some flexibility to increase or
decrease the weight associated with certain k-mers or features. Increase
can be achieved through repetition, and some features can be assigned
a negative weight through a ``data_neg`` field.

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
skewed in favor of feature ``B`` compared to the representation of ``item:single``.

The numeric representation of ``item:negative`` will include a negative for
feature ``B``.


Numeric weighting
~~~~~~~~~~~~~~~~~

To achieve more control over the weighting of certain feature, the
items can be specified through a field ``value`` instead of ``data``.

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

Specifying values for each feature gives explicit control over the relative
weighting between features.

Note that whereas text under ``data`` is parsed automatically into k-mers
and then used to to construct a numeric representation, features
under ``value`` are used as-is.

Note that the ``data`` and ``value`` fields can be specified together.
However, it is not clear from the data file how these two components will be
weighted.

