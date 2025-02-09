""" This file contains hard-coded values used in the integration test
test_upwind_coupling.test_upwind_coupling_3d_2d_1d_0d()

The values are moved into a separate file to avoid poluting the file
containing tests.

"""
import numpy as np
import scipy.sparse as sps


def matrix_rhs_for_test_upwind_coupling_3d_2d_1d_0d():

    indptr = np.array(
        [
            0,
            3,
            7,
            10,
            14,
            17,
            21,
            24,
            28,
            32,
            37,
            41,
            46,
            50,
            54,
            58,
            62,
            66,
            71,
            75,
            80,
            85,
            90,
            95,
            101,
            106,
            111,
            117,
            118,
            119,
            120,
            121,
            122,
            123,
            124,
            125,
            127,
            129,
            131,
            133,
            135,
            137,
            139,
            141,
            142,
            143,
            144,
            145,
            146,
            147,
            148,
            149,
            150,
            151,
            153,
            155,
            156,
            157,
            159,
            161,
            163,
            165,
            167,
            169,
            171,
            173,
            175,
            177,
            178,
            179,
            181,
            183,
            184,
            185,
            187,
            189,
            191,
            192,
            193,
            195,
            196,
            197,
        ],
        dtype=np.int32,
    )

    indices = np.array(
        [
            31,
            40,
            47,
            1,
            32,
            36,
            48,
            33,
            42,
            43,
            3,
            34,
            38,
            44,
            27,
            39,
            49,
            5,
            28,
            35,
            50,
            29,
            41,
            45,
            7,
            30,
            37,
            46,
            27,
            31,
            52,
            54,
            9,
            28,
            32,
            53,
            56,
            29,
            33,
            51,
            58,
            11,
            30,
            34,
            55,
            57,
            35,
            39,
            60,
            62,
            36,
            40,
            59,
            66,
            37,
            41,
            61,
            64,
            38,
            42,
            63,
            65,
            43,
            47,
            68,
            74,
            17,
            44,
            48,
            72,
            73,
            45,
            49,
            67,
            70,
            19,
            46,
            50,
            69,
            71,
            51,
            52,
            67,
            68,
            75,
            53,
            54,
            59,
            60,
            76,
            61,
            62,
            69,
            70,
            77,
            23,
            55,
            56,
            71,
            72,
            78,
            57,
            58,
            63,
            64,
            79,
            65,
            66,
            73,
            74,
            80,
            75,
            76,
            77,
            78,
            79,
            80,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            34,
            12,
            35,
            13,
            36,
            14,
            37,
            15,
            38,
            4,
            39,
            0,
            40,
            6,
            41,
            2,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            21,
            53,
            8,
            54,
            55,
            56,
            24,
            57,
            10,
            58,
            21,
            59,
            12,
            60,
            22,
            61,
            12,
            62,
            24,
            63,
            14,
            64,
            25,
            65,
            13,
            66,
            67,
            68,
            22,
            69,
            18,
            70,
            71,
            72,
            25,
            73,
            16,
            74,
            20,
            75,
            76,
            77,
            26,
            78,
            79,
            80,
        ],
        dtype=np.int32,
    )

    data = np.array(
        [
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            2.50000000e-01,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            2.50000000e-01,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            2.50000000e-01,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            2.50000000e-01,
            1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            5.00000000e-03,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            5.00000000e-03,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            5.00000000e-03,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            5.00000000e-03,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            1.00000000e-04,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -2.50000000e-01,
            -1.00000000e00,
            -2.50000000e-01,
            -1.00000000e00,
            -2.50000000e-01,
            -1.00000000e00,
            -2.50000000e-01,
            -1.00000000e00,
            2.50000000e-01,
            -1.00000000e00,
            2.50000000e-01,
            -1.00000000e00,
            2.50000000e-01,
            -1.00000000e00,
            2.50000000e-01,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -5.00000000e-03,
            -1.00000000e00,
            5.00000000e-03,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -5.00000000e-03,
            -1.00000000e00,
            5.00000000e-03,
            -1.00000000e00,
            -5.55111512e-19,
            -1.00000000e00,
            5.55111512e-19,
            -1.00000000e00,
            -5.55111512e-19,
            -1.00000000e00,
            5.55111512e-19,
            -1.00000000e00,
            -5.55111512e-19,
            -1.00000000e00,
            5.55111512e-19,
            -1.00000000e00,
            -5.55111512e-19,
            -1.00000000e00,
            5.55111512e-19,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -5.00000000e-03,
            -1.00000000e00,
            5.00000000e-03,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -5.00000000e-03,
            -1.00000000e00,
            5.00000000e-03,
            -1.00000000e00,
            1.00000000e-04,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e-04,
            -1.00000000e00,
            -1.00000000e00,
            -1.00000000e00,
        ]
    )

    U = sps.csr_matrix((data, indices, indptr), shape=(81, 81)).toarray()

    rhs = np.array(
        [
            2.5e-01,
            0.0e00,
            2.5e-01,
            0.0e00,
            2.5e-01,
            0.0e00,
            2.5e-01,
            0.0e00,
            5.0e-03,
            0.0e00,
            5.0e-03,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            5.0e-03,
            0.0e00,
            5.0e-03,
            0.0e00,
            1.0e-04,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
            0.0e00,
        ]
    )
    return U, rhs
