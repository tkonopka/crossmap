"""Computing nearest neighbors using sparse matrices

@author: Tomasz Konopka
"""

from sklearn.metrics import pairwise_distances


def neighbors(query, x, n_neighbors=1):
    """Find n_neighbors items in X that are nearest to the query.

    Arguments:
        query         csr array with one row
        x             csr array with many items, shape (num samples, num features)
        n_neighbors   integer, number of nearest neighbors to find

    Returns
        Array of size (n_neighbors) with row indexes in x
    """

    distances = pairwise_distances(query, x)[0]
    data = [(distances[i], i) for i in range(len(distances))]
    data.sort()
    return [data[i][1] for i in range(n_neighbors)]
