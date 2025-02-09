"""
Test the mcolon function
"""
import unittest

import numpy as np

from porepy.utils import mcolon


class TestMColon(unittest.TestCase):
    def test_mcolon_simple(self):
        a = np.array([1, 2])
        b = np.array([3, 4])
        c = mcolon.mcolon(a, b)
        self.assertTrue(np.all((c - np.array([1, 2, 2, 3])) == 0))

    def test_mcolon_zero_output(self):
        a = np.array([1, 2])
        b = np.array([1, 2])
        c = mcolon.mcolon(a, b)
        self.assertTrue(c.size == 0)

    def test_mcolon_one_missing(self):
        a = np.array([1, 2])
        b = np.array([3, 1])
        c = mcolon.mcolon(a, b)
        self.assertTrue(np.all((c - np.array([1, 2])) == 0))

    def test_mcolon_middle_equal(self):
        # Motivated by GitHub issue #11
        indPtr = np.array([1, 5, 5, 6])
        select = np.array([0, 1, 2])

        c = mcolon.mcolon(indPtr[select], indPtr[select + 1])
        c_known = np.array([1, 2, 3, 4, 5])
        self.assertTrue(np.allclose(c, c_known))

    def test_mcolon_last_equal(self):
        # Motivated by GitHub issue #11
        indPtr = np.array([1, 5, 5, 6])
        select = np.array([0, 1])

        c = mcolon.mcolon(indPtr[select], indPtr[select + 1])
        c_known = np.array([1, 2, 3, 4])
        self.assertTrue(np.allclose(c, c_known))

    def test_hi_low_same_size(self):
        a = np.array([1, 2])
        b = np.array([2, 3, 4])
        self.assertRaises(ValueError, mcolon.mcolon, a, b)

    def test_type_conversion(self):
        a = np.array([1, 3], dtype=np.int8)
        b = 1 + np.array([1, 3], dtype=np.int16)
        c = mcolon.mcolon(a, b)
        self.assertTrue(c.dtype == int)


if __name__ == "__main__":
    unittest.main()
