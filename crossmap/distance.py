"""
Distance calculations
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
def all_zero(a):
    """evaluate if entire vector is made up of zeros"""
    for i in range(len(a)):
        if a[i] != 0.0:
            return 0
    return 1


@numba.jit
def num_nonzero(a):
    """evaluate number of elements in a vector that are nonzero"""
    result = 0
    for i in range(len(a)):
        result += (a[i]!=0.0)
    return result


@numba.jit
def normalize_vec(a):
    """compute the vector norm of a vector"""
    n = vec_norm(a)
    if n == 0:
        return a
    for i in range(len(a)):
        a[i] = a[i]/n
    return a


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

