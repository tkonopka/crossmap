'''Tests for computing embedding with umap
'''

import unittest
import numpy as np
import warnings
from scipy.sparse import csr_matrix

mm = np.random.rand(30,3)-0.5
mm.shape = (30, 3)
ss = csr_matrix(mm)

@unittest.skip
class UmapTests(unittest.TestCase):
    """Computing embeddings with umap"""

    def test_with_csr(self):
        """Compute embedding based on raw data in a csr matrix"""

        mm = np.random.rand(90)
        mm.shape = (30, 3)
        ss = csr_matrix(mm)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            u = umap.UMAP()
            result = u.fit(ss)
        self.assertEqual(len(result.embedding_[:,0]), mm.shape[0])

