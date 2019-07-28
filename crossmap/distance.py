"""Distance calculations
"""

import numba
from math import sqrt


@numba.jit
def vec_norm(a):
    """compute the vector norm of a vector"""

    sum2 = 0
    for i in range(len(a)):
        sum2 += a[i] *a[i]
    return sqrt(sum2)


@numba.jit
def euc_dist(a, b):
    """compute the euclidean distance between two vectors"""

    dist2 = 0
    for i in range(len(a)):
        dist2 += (a[i]-b[i])*(a[i]-b[i])
    return sqrt(dist2)


@numba.jit
def euc_sq_dist(a, b):
    """compute the squared euclidean distance between two vectors"""

    dist2 = 0
    for i in range(len(a)):
        dist2 += (a[i]-b[i])*(a[i]-b[i])
    return dist2

