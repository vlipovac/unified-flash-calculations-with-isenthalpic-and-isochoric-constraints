import numpy as np
import unittest

from porepy.numerics.darcyEq import DarcyData
from porepy.grids import simplex
from porepy.params import bc, tensor
from porepy.params.data import Parameters

#------------------------------------------------------------------------------#


class BasicsTest(unittest.TestCase):

    #------------------------------------------------------------------------------#

    def test_darcy_data_default_values(self):
        """
        test that the darcy data initialize the correct data.
        """
        p = np.random.rand(3, 10)
        g = simplex.TetrahedralGrid(p)
        param = Parameters(g)
        darcy_data = dict()
        DarcyData(g, darcy_data)
        darcy_param = darcy_data['param']

        check_parameters(darcy_param, param)

    def test_darcy_data_given_values(self):
        """
        test that the darcy data initialize the correct data.
        """
        p = np.random.rand(3, 10)
        g = simplex.TetrahedralGrid(p)
        # Set values
        bc_val = np.pi * np.ones(g.num_faces)
        dir_faces = g.get_boundary_faces()
        bc_cond = bc.BoundaryCondition(g, dir_faces, ['dir'] * dir_faces.size)
        porosity = 1 / np.pi * np.ones(g.num_cells)
        apperture = 0.5 * np.ones(g.num_cells)
        kxx = 2 * np.ones(g.num_cells)
        kyy = 3 * np.ones(g.num_cells)
        K = tensor.SecondOrder(g.dim, kxx, kyy)
        source = 42 * np.ones(g.num_cells)
        # Assign to parameter
        param = Parameters(g)
        param.set_bc_val('flow', bc_val)
        param.set_bc('flow', bc_cond)
        param.set_porosity(porosity)
        param.set_aperture(apperture)
        param.set_tensor('flow', K)
        param.set_source('flow', source)
        # Define DarcyData class

        class Data(DarcyData):
            def __init__(self, g, data):
                DarcyData.__init__(self, g, data)

            def bc(self):
                return bc_cond

            def bc_val(self):
                return bc_val

            def porosity(self):
                return porosity

            def aperture(self):
                return apperture

            def permeability(self):
                return K

            def source(self):
                return source

        darcy_data = dict()
        Data(g, darcy_data)
        darcy_param = darcy_data['param']

        check_parameters(darcy_param, param)


#------------------------------------------------------------------------------#


def check_parameters(param_c, param_t):

    bc_c = param_c.get_bc('flow')
    bc_t = param_t.get_bc('flow')
    k_c = param_c.get_tensor('flow').perm
    k_t = param_t.get_tensor('flow').perm

    assert np.alltrue(bc_c.is_dir == bc_t.is_dir)
    assert np.alltrue(param_c.get_bc_val('flow') == param_t.get_bc_val('flow'))
    assert np.alltrue(param_c.get_porosity() == param_t.get_porosity())
    assert np.alltrue(param_c.get_aperture() == param_t.get_aperture())
    assert np.alltrue(k_c == k_t)
    assert np.alltrue(param_c.get_source('flow') == param_t.get_source('flow'))
