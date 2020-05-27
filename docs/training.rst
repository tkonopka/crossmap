User-driven learning
====================

``crossmap`` instances are not static. In particular, they can create
and populate new data collections. This capability to add data items
into a collection, together with the flexibility to use data diffusion,
provides a mechanism to train the instance.

To demonstrate this procedure, consider a ``crossmap`` instance that
stores a dictionary of English words
(from the `wiktionary <https://www.wiktionary.org/>`_). Diffusion driven
from this dataset reveals features that co-occur in the dictionary,
and thus likely have related meanings.

.. image:: img/training_before.png
   :alt: diffusion prior to user-driven training

In the above example, the diffusion of the word 'gait' reveals imputed
values for 'walk', 'move', and many other terms.

Let's suppose an important related feature is missing, or weighted
incorrectly. As an example, let's say that 'gait' should strongly diffuse
into 'walking'. We can adjust the diffusion profile via user-driven learning.
To access the graphical interface for this, use the drop-down box on the
left-hand-side of the controller to select 'Train'.

.. image:: img/training.png
   :alt: training form

The form requires specifying the dataset to augment. The above example creates
a new dataset called ``manual`` with a new data item that consists of the words
`gait` and `walking` together. The form also allows for creating a title for the
data object and adding a comment / metadata. After clicking SEND, the chat
will record that a new item has been added to the database.

After the new dataset is created, it becomes possible to use that collection
to drive diffusion.

.. image:: img/training_after.png
   :alt: diffusion after user-driven learning

In this example, the diffusion is driven by the wiktionary and by the manual
dataset. The diffusion profile looks similar to before, but with more emphasis
on features from the word 'walking'.

When combined with search or with decomposition, the modifed diffusion profile
can result in personalized outputs from those algorithms.


