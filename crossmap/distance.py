"""
Distance calculations
"""

import numba
from math import sqrt
from .vectors import vec_norm

@numba.jit
def norm_euc_dist(a, b):
    """compute the euclidean distance between two vectors"""

    anorm = vec_norm(a)
    bnorm = vec_norm(b)
    for i in range(len(a)):
        a[i] = a[i] / anorm
        b[i] = b[i] / bnorm
    dist2 = 0
    for i in range(len(a)):
        dist2 += (a[i]-b[i])*(a[i]-b[i])
    return sqrt(dist2)


@numba.jit
def euc_dist(a, b):
    """compute the euclidean distance between two vectors"""

    dist2 = 0
    for i in range(len(a)):
        dist2 += (a[i]-b[i])*(a[i]-b[i])
    return sqrt(dist2)

