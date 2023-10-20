from thermo import PR78MIX, CEOSGas, CEOSLiquid, ChemicalConstantsPackage, FlashVLN
from thermo.interaction_parameters import IPDB

import porepy as pp
import numpy as np

verbosity = 2
SPECIES: list[str] = ["H2O", "CO2"]
FEED: list[float] = [0.99, 0.01]

SPECIES_geo: list[str] = ["H2O", "CO2", "H2S", "N2"]
FEED_geo: list[float] = [0.8, 0.05, 0.1, 0.05]

vec = np.ones(1)

p = 22153846.153846152
p = 22692307.692307692
p = 22871794.871794872
T = 300
h = -1435.8974358974356
h = -1435.8974358974356
h = 1512.8205128205118


def _thermo_init(species=SPECIES) -> FlashVLN:
    """Helper function to initiate the thermo flash."""
    constants, properties = ChemicalConstantsPackage.from_IDs(species)
    kijs = IPDB.get_ip_asymmetric_matrix("ChemSep PR", constants.CASs, "kij")
    eos_kwargs = {
        "Pcs": constants.Pcs,
        "Tcs": constants.Tcs,
        "omegas": constants.omegas,
        "kijs": kijs,
    }

    GAS = CEOSGas(
        PR78MIX, eos_kwargs=eos_kwargs, HeatCapacityGases=properties.HeatCapacityGases
    )
    LIQs = [
        CEOSLiquid(
            PR78MIX,
            eos_kwargs=eos_kwargs,
            HeatCapacityGases=properties.HeatCapacityGases,
        )
        for _ in range(len(species))
    ]
    flasher = FlashVLN(constants, properties, liquids=LIQs, gas=GAS)

    return flasher


thermo_flash = _thermo_init(SPECIES_geo)
thermo_r = thermo_flash.flash(P=p, H=h, zs=FEED_geo)
print("----")
print(f"T Thermo = {float(thermo_r.T)}")
print(f"y Thermo = {float(thermo_r.VF)}")



### Setting up the fluid mixture
species = pp.composite.load_species(SPECIES_geo)

# Components using specific models for ideal enthalpies.
comps = [
    pp.composite.peng_robinson.H2O.from_species(species[0]),
    pp.composite.peng_robinson.CO2.from_species(species[1]),
    pp.composite.peng_robinson.H2S.from_species(species[2]),
    pp.composite.peng_robinson.N2.from_species(species[3]),
]

phases = [
    pp.composite.Phase(
        pp.composite.peng_robinson.PengRobinsonEoS(gaslike=False), name="L"
    ),
    pp.composite.Phase(
        pp.composite.peng_robinson.PengRobinsonEoS(gaslike=True), name="G"
    ),
]

mix = pp.composite.NonReactiveMixture(comps, phases)

mix.set_up()

### Setting feed fraction values using PorePy's AD framework
[
    mix.system.set_variable_values(val * vec, [comp.fraction.name], 0, 0)
    for val, comp in zip(FEED_geo, comps)
]

### Flash object and solver settings
flash = pp.composite.FlashNR(mix)
flash.use_armijo = True
flash.armijo_parameters["rho"] = 0.99
flash.armijo_parameters["j_max"] = 30
flash.armijo_parameters["return_max"] = True
flash.initialization_parameters = {
    'N1': 3,
    'N2': 1,
    'N3': 5,
}
flash.newton_update_chop = 1.0
flash.tolerance = 1e-8
flash.max_iter = 200

### p-T flash
### Other flash types are performed analogously.
# flash._T_guess = 733.4821859121463
success, results = flash.flash(
    state={"p": p * vec, "h": h * vec},
    eos_kwargs={"apply_smoother": True},
    feed=[vec * z for z in FEED_geo],
    verbosity=verbosity,
    quickshot=False
)
print("Results:\n" + "------------")
print(str(results))
print("------------")