"""Contains concrete implementation of phases."""

from typing import List

import iapws

from ..phase import PhaseField
from .fluid_substances import H20_iapws
from .solid_substances import NaCl_simple

__all__: List[str] = ["SaltWater_iapws", "WaterVapor_iapws"]


class SaltWater_iapws(PhaseField):
    pass


class WaterVapor_iapws(PhaseField):
    pass
