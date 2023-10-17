"""This script is an example of how to run a flash using the PorePy package.

It is devised for the publication
``Unified flash calculations with isenthalpic and isochoric constraints``
and does not necessarily work with other versions of PorePy.

Use only in combination with the version contained in the publication-accompanying
docker image.

"""

import numpy as np

import porepy as pp

chems = ["H2O", "CO2", "H2S", "N2"]

vec = np.ones(1)
# feed fractions
z = [vec * 0.8,  vec * 0.05, vec * 0.1, vec * 0.05]
# pressure
p = vec * 20368421.05263158
# temperature
T = vec * 350.0
# enthalpy
h = vec  * 11368.421052631578
# verbosity for logs during flash
verbosity = 2

### Setting up the fluid mixture
species = pp.composite.load_species(chems)

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
    mix.system.set_variable_values(val, [comp.fraction.name], 0, 0)
    for val, comp in zip(z, comps)
]

### Flash object and solver settings
flash = pp.composite.FlashNR(mix)
flash.use_armijo = True
flash.armijo_parameters["rho"] = 0.99
flash.armijo_parameters["j_max"] = 50
flash.armijo_parameters["return_max"] = True
flash.newton_update_chop = 1.0
flash.tolerance = 1e-7
flash.max_iter = 150

### p-T flash
### Other flash types are performed analogously.
flash._T_guess = 733.4821859121463
success, results = flash.flash(
    # state={"p": p, "T": T},
    state={"p": p, "h": h},
    eos_kwargs={"apply_smoother": True},
    feed=z,
    verbosity=verbosity,
)
print("Results:\n" + "------------")
print(str(results))
print("------------")
