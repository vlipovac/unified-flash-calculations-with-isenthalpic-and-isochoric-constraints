# -*- coding: utf-8 -*-
"""
Created on Fri Mar  4 09:04:16 2016

@author: eke001
"""

import numpy as np
import scipy.sparse as sps

from utils import matrix_compression
from utils import mcolon


def compute_dist_face_cell(g, cno, fno, nno, subhfno, eta):
    _ , blocksz = matrix_compression.rlencode(np.vstack((cno, nno)))
    dims = g.dim

    i, j = np.meshgrid(subhfno, np.arange(dims))
    j += matrix_compression.rldecode(np.cumsum(blocksz)-blocksz[0], blocksz)
    
    etaVec = eta*np.ones(fno.size)
    # Set eta values to zero at the boundary
    bnd = np.argwhere(np.abs(g.cellFaces).sum(axis=1).A.squeeze() 
                            == 1).squeeze()
    etaVec[bnd] = 0
    cp = g.faceCenters[:, fno] + etaVec * (g.nodes[:, nno] - 
                                g.faceCenters[:, fno])
    dist = cp - g.cellCenters[:, cno]
    return sps.coo_matrix((dist.ravel(), (i.ravel(), j.ravel()))).tocsr()

@profile
def invert_diagonal_blocks(A, sz):
    v = np.zeros(np.sum(np.square(sz)))
    p1 = 0
    p2 = 0
    for b in range(sz.size):
        n = sz[b]
        n2 = n * n
        i = p1 + np.arange(n+1)
        #vals = A.A[i[0]:i[-1], i[0]:i[-1]]
        v[p2 + np.arange(n2)] = np.linalg.inv(A[i[0]:i[-1], i[0]:i[-1]].A)
        p1 = p1 + n
        p2 = p2 + n2
    iA = block_diag_matrix(v, sz)
    return iA


def block_diag_matrix(v, sz):
    i, j = block_diag_index(sz)
    return sps.coo_matrix((v, (j, i))).tocsr()


def block_diag_index(m, n=None):
    """
    >>> m = np.array([2, 3])
    >>> n = np.array([1, 2])
    >>> i, j = block_diag_index(m, n)
    >>> i, j
    (array([0, 1, 2, 3, 4, 2, 3, 4]), array([0, 0, 1, 1, 1, 2, 2, 2]))
    >>> a = np.array([1, 3])
    >>> i, j = block_diag_index(a)
    >>> i, j
    (array([0, 1, 2, 3, 1, 2, 3, 1, 2, 3]), array([0, 1, 1, 1, 2, 2, 2, 3, 3, 3]))
    """
    if n is None:
        n = m

    start = np.hstack((np.zeros(1), m))
    pos = np.cumsum(start)
    p1 = pos[0:-1]
    p2 = pos[1:]-1
    p1_full = matrix_compression.rldecode(p1, n)
    p2_full = matrix_compression.rldecode(p2, n)

    i = mcolon.mcolon(p1_full, p2_full)
    sumn = np.arange(np.sum(n))
    m_n_full = matrix_compression.rldecode(m, n)
    j = matrix_compression.rldecode(sumn, m_n_full)
    return i, j
    
if __name__ == '__main__':
    block_diag_index(np.array([2, 3]))
