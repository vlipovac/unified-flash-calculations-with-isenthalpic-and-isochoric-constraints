"""Configuration file containing data range values and functionality for calculating
and plotting data."""
from __future__ import annotations

import csv
import logging
import pathlib
import sys
import time
from ctypes import c_double, c_uint8
from multiprocessing import Array, Pool, Process, Queue, RawArray
from multiprocessing.pool import AsyncResult
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import psutil
from matplotlib import figure
from matplotlib.colors import LinearSegmentedColormap
from thermo import PR78MIX, CEOSGas, CEOSLiquid, ChemicalConstantsPackage, FlashVLN
from thermo.interaction_parameters import IPDB

import porepy as pp

sys.path.append(str(pathlib.Path(__file__).parent.resolve()))

from batlow import cm_data as batlow_data

# figure configurations
# in inches, all plots are square, error plots have a aspect ratio of 1:3
FIGURE_WIDTH: int = 10
# height-to-width ratio per plot
# This is not applied to error plots
ASPECT_RATIO: float = 0.8
DPI: int = 400  # Dots per Inch (level of detail per figure)
FIGURE_FORMAT: str = "png"
MARKER_SCALE: int = 2  # Size scaling of markers in legend
MARKER_SIZE: int = 10

# Defining colors for plots
batlow_map = LinearSegmentedColormap.from_list("batlow", batlow_data)
NA_COL = batlow_map(0.0)  # color for not available data
LIQ_COL = batlow_map(0.25)  # color for liquid phase
MPHASE_COL = batlow_map(0.5)  # color for multi-phase region
GAS_COL = batlow_map(0.75)  # color for gas phase
GAS_COL_2 = batlow_map(1.0)  # Additional color for gas phase (Widom extension)
WHITE_COL = (1, 1, 1, 1)
BLACK_COL = (0, 0, 0, 1)
GREY_COL = (0.5, 0.5, 0.5, 1)

# Calculation modus for PorePy flash
# 1 - point-wise (robust, but possibly very slow),
# 3 - parallelized (use with care, if system compatible)
CALCULATION_MODE: int = 3

# fluid mixture configuration
SPECIES: list[str] = ["H2O", "CO2"]
FEED: list[float] = [0.99, 0.01]

# pressure and temperature limits for p-T calculations
P_LIMITS: list[float] = [1e6, 50e6]  # [Pa]
T_LIMITS: list[float] = [450.0, 700.0]  # [K]
# resolution of p-T limits
RESOLUTION_pT: int = 50

# temperature values for isotherms for p-h calculations
# more refined around critical temperature of water, up to critical pressure of water
ISOTHERMS: list[float] = [500.0, 550.0, 600, 645.0, 647.14, 650.0]
P_LIMITS_ISOTHERMS: list[float] = [1e6, 23000000.0]
# pressure resolution along isotherms
RESOLUTION_ph: int = 20

# Isobar and isotherm for h-v calculations
HV_ISOBAR: float = 15e6
HV_ISOBAR_T_LIMITS: list[float] = [575, 630]
HV_ISOTHERM: float = 575.0
HV_ISOTHERM_P_LIMITS: list[float] = [5e6, 15e6]
# pressure and temperature resolution for isobar and isotherm for h-v flash
RESOLUTION_hv: int = 10

# Limits for A and B when plotting te roots
A_LIMITS: list[float] = [0, 2 * pp.composite.peng_robinson.PengRobinsonEoS.A_CRIT]
B_LIMITS: list[float] = [0, 2 * pp.composite.peng_robinson.PengRobinsonEoS.B_CRIT]
RESOLUTION_AB: int = 300

# Widom line for water: Pressure and Temperature values
WIDOM_LINE: list[np.ndarray] = [
    np.array([225, 250, 270]) * 1e5,  # bar to Pa
    np.array([646.9, 655.6, 664.9]),
]

# Scaling for plots
PRESSURE_SCALE: float = 1e-6  # to MPa
PRESSURE_SCALE_NAME: str = "MPa"

# paths to where results should be stored
THERMO_DATA_PATH: str = "data/thermodata.csv"  # storing results from therm
PT_FLASH_DATA_PATH: str = "data/flash_pT.csv"  # storing p-T results from porepy
ISOTHERM_DATA_PATH: str = (
    "data/flash_pT_isotherms.csv"  # storing p-T results on isotherms
)
PH_FLASH_DATA_PATH: str = "data/flash_ph.csv"  # storing p-h results from porepy
HV_ISOTHERM_DATA_PATH: str = (
    "data/flash_hv_isotherm.csv"  # storing p-T results on isotherm for h-v flash
)
HV_ISOBAR_DATA_PATH: str = (
    "data/flash_hv_isobar.csv"  # storing p-T results on isobar for h-v flash
)
HV_FLASH_DATA_PATH: str = "data/flash_hv.csv"  # storing h-v results from porepy
FIG_PATH: str = "figs/"  # path to folder containing plots

NUM_COMP: int = len(SPECIES)  # number of components
DELIMITER: str = ","  # delimiter in result files
# entry for a points which are missing, have no meaning or the flash failed
NAN_ENTRY: np.nan = np.nan
# Phase labels, G L1 L2 ...
PHASES: list[str] = ["G"] + [f"L{i}" for i in range(1, NUM_COMP + 1)]
# headers in result files
success_HEADER: str = "success"
num_iter_HEADER: str = "num-iter"
conditioning_HEADER: str = "condition-number"
phases_HEADER: str = "phase-split"
p_HEADER: str = "p [Pa]"
T_HEADER: str = "T [K]"
h_HEADER: str = "h [J/mol]"
v_HEADER: str = "v [m^3]"
gas_satur_HEADER: str = "s"
liq_satur_HEADER: str = [f"s_L{j}" for j in range(1, NUM_COMP + 1)]
gas_frac_HEADER: str = "y"
liq_frac_HEADER: list[str] = [f"y_L{j}" for j in range(1, NUM_COMP + 1)]
composition_HEADER: dict[str, dict[str, str]] = dict(
    [(i, dict([(f"{j}", f"x_{i}_{j}") for j in PHASES])) for i in SPECIES]
)
compressibility_HEADER: dict[str, str] = dict([(f"{j}", f"Z_{j}") for j in PHASES])
fugacity_HEADER: dict[str, dict[str, str]] = dict(
    [(i, dict([(f"{j}", f"phi_{i}_{j}") for j in PHASES])) for i in SPECIES]
)

# Number of physical CPU cores.
# This is used for the number of sub-processes and chunksize in the parallelization
NUM_PHYS_CPU_CORS = psutil.cpu_count(logical=False)


logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler()
log_handler.terminator = ""
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

del_log = "\r" + " " * 100 + "\r"


def path():
    """Returns path to script calling this function as string."""
    return str(pathlib.Path(__file__).parent.resolve())


def read_data_column(
    file_path: str,
    header: str,
) -> tuple[list[float], list[float]]:
    """Reads a data column from a file."""
    points: list[float] = list()

    logger.info(f"{del_log}Reading data column {header} from file {file_path}")
    with open(f"{path()}/{file_path}", "r") as csvfile:
        reader = csv.reader(csvfile, delimiter=DELIMITER)
        headers = next(reader)  # get rid of header
        if header not in headers:
            raise ValueError(f"Header {header} not found in file {file_path}")

        idx = headers.index(header)

        for row in reader:

            # must always be available
            x = float(row[idx])
            # potentially missing or nan
            if x not in [NAN_ENTRY, str(NAN_ENTRY)]:
                x = float(x)
            else:
                x = NAN_ENTRY

            points.append(x)
    logger.info(f"{del_log}Reading data column {header}: done\n")
    return points


def create_index_map(x: list[float], y: list[float]) -> dict[tuple[float, float], int]:
    """Creates a index map to associate a tuple of data found in x and y with their
    index.

    Use this in combination with ``read_px_data`` to access specific values in a results
    data structure created by ``read_results``.

    """
    return dict([((xy[0], xy[1]), i) for i, xy in enumerate(zip(x, y))])


def read_results(file_name: str, headers: list[str] | None = None) -> dict[str, list]:
    """Reads data previously written with ``write_results``.

    Use ``headers`` to specify which header to read.
    Otherwise all columns are read.

    The returned dictionary contains per header the data column.

    """

    logger.info(f"{del_log}Reading result data: file {file_name}")
    with open(f"{path()}/{file_name}", mode="r") as file:
        reader = csv.reader(file, delimiter=DELIMITER)

        file_headers = next(reader)
        if headers is None:
            headers = file_headers

        data: dict[str, list] = dict([(head, list()) for head in headers])
        header_idx: dict[str, int] = dict(
            [(head, file_headers.index(head)) for head in headers]
        )

        for row in reader:
            for head in headers:
                idx = header_idx[head]
                d = row[idx]
                data[head].append(d)
    logger.info(f"{del_log}Reading result data: done\n")

    return data


def write_results(filename: str, results: dict[str, list]):
    """Writes results to file. Results must be a dictionary with headers as keys
    and data columns as values."""
    headers = [header for header, _ in results.items()]
    data = [col for _, col in results.items()]

    logger.info(f"{del_log}Writing result data: file {filename}")
    with open(f"{path()}/{filename}", "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=DELIMITER)
        # wrting header
        writer.writerow(headers)
        # writing data
        for row in zip(*data):
            writer.writerow(row)
    logger.info(f"{del_log}Writing result data: done\n")


def _thermo_init() -> FlashVLN:
    """Helper function to initiate the thermo flash."""
    constants, properties = ChemicalConstantsPackage.from_IDs(SPECIES)
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
        for _ in range(NUM_COMP)
    ]
    flasher = FlashVLN(constants, properties, liquids=LIQs, gas=GAS)

    return flasher


def _init_empty_results() -> dict[str, list]:
    """Initiate and return an results dict with proper headers as needed for the
    comparison."""
    results: dict[str, list] = {
        success_HEADER: list(),
        num_iter_HEADER: list(),
        conditioning_HEADER: list(),
        p_HEADER: list(),
        T_HEADER: list(),
        h_HEADER: list(),
        v_HEADER: list(),
        phases_HEADER: list(),
        gas_satur_HEADER: list(),
    }
    results.update(dict([(liq_satur_HEADER[i], list()) for i in range(NUM_COMP)]))
    results.update({gas_frac_HEADER: list()})
    results.update(dict([(liq_frac_HEADER[i], list()) for i in range(NUM_COMP)]))
    results.update(dict([(compressibility_HEADER[j], list()) for j in PHASES]))
    results.update(
        dict([(composition_HEADER[i][j], list()) for j in PHASES for i in SPECIES])
    )
    results.update(
        dict([(fugacity_HEADER[i][j], list()) for j in PHASES for i in SPECIES])
    )

    return results


def _thermo_parse_result(state) -> dict:
    """Helper function to parse a state returned by thermo into processable format."""
    out = _init_empty_results()
    for k in out.keys():
        out[k] = NAN_ENTRY

    out.update(
        {
            success_HEADER: 0,
            gas_frac_HEADER: state.VF,
        }
    )
    # anticipate at max only 1 gas phase and predefined number of liquid phases
    if 0 < state.phase_count <= 1 + NUM_COMP:
        if (
            0.0 < state.VF <= 1.0
        ) and state.gas is not None:  # parse gas phase if present
            j = PHASES[0]
            out.update(
                {
                    phases_HEADER: j,
                    compressibility_HEADER[j]: state.gas.Z(),
                }
            )
            out.update(
                dict(
                    [
                        (composition_HEADER[i][j], state.gas.zs[SPECIES.index(i)])
                        for i in SPECIES
                    ]
                    + [
                        (fugacity_HEADER[i][j], state.gas.phis()[SPECIES.index(i)])
                        for i in SPECIES
                    ]
                )
            )
        # should not happen
        elif (state.gas is None and (0.0 < state.VF <= 1.0)) or (
            state.gas is not None and state.VF == 0.0
        ):
            raise NotImplementedError(
                f"Uncovered thermo phase case: conflicting gas state"
            )
        else:  # gas phase is not present, store nans
            assert state.VF == 0.0, "Uncovered thermo gas phase state."
            j = PHASES[0]
            out.update(
                {
                    phases_HEADER: "",
                    compressibility_HEADER[j]: NAN_ENTRY,
                }
            )
            out.update(
                dict(
                    [(composition_HEADER[i][j], NAN_ENTRY) for i in SPECIES]
                    + [(fugacity_HEADER[i][j], NAN_ENTRY) for i in SPECIES]
                )
            )

        if (
            state.gas is not None and state.VF == 1.0
        ):  # if only gas, fill liquid entries with nans
            # for anticipated liquid phases
            for liq_frac in liq_frac_HEADER:
                out.update({liq_frac: 0.0})
            for j in PHASES[1:]:
                out.update(
                    {
                        compressibility_HEADER[j]: NAN_ENTRY,
                    }
                )
                out.update(
                    dict(
                        [(composition_HEADER[i][j], NAN_ENTRY) for i in SPECIES]
                        + [(fugacity_HEADER[i][j], NAN_ENTRY) for i in SPECIES]
                    )
                )
        else:  # parse present liquid phases
            # sanity check
            assert (
                state.VF < 1.0
            ), "Thermo conflicting gas state: Gas saturated with liquid phases"
            if len(state.liquids) == 1:  # if only one liquid phase
                out[phases_HEADER] = out[phases_HEADER] + "L"
                j = PHASES[1]
                out.update({liq_frac_HEADER[0]: 1 - state.VF})
                for yl in liq_frac_HEADER[1:]:
                    out.update({yl: NAN_ENTRY})
                out.update(
                    {
                        compressibility_HEADER[j]: state.liquids[0].Z(),
                    }
                )
                out.update(
                    dict(
                        [
                            (
                                composition_HEADER[i][j],
                                state.liquids[0].zs[SPECIES.index(i)],
                            )
                            for i in SPECIES
                        ]
                        + [
                            (
                                fugacity_HEADER[i][j],
                                state.liquids[0].phis()[SPECIES.index(i)],
                            )
                            for i in SPECIES
                        ]
                    )
                )
                # fill other liquid phases with nans
                for j in PHASES[2:]:
                    out.update(
                        {
                            compressibility_HEADER[j]: NAN_ENTRY,
                        }
                    )
                    out.update(
                        dict(
                            [(composition_HEADER[i][j], NAN_ENTRY) for i in SPECIES]
                            + [(fugacity_HEADER[i][j], NAN_ENTRY) for i in SPECIES]
                        )
                    )
            elif 1 < len(state.liquids) <= NUM_COMP:  # get all liquid data
                assert (
                    state.liquids_betas
                ), "Thermo conflicting liquid phase state: no liquid betas"
                for i in range(NUM_COMP):
                    out.update({liq_frac_HEADER[i]: state.liquids_betas[i]})
                for p_idx, j in enumerate(PHASES[1:]):
                    out[phases_HEADER] = out[phases_HEADER] + "L"
                    out.update(
                        {
                            compressibility_HEADER[j]: state.liquids[p_idx].Z(),
                        }
                    )
                    out.update(
                        dict(
                            [
                                (
                                    composition_HEADER[i][j],
                                    state.liquids[p_idx].zs[SPECIES.index(i)],
                                )
                                for i in SPECIES
                            ]
                            + [
                                (
                                    fugacity_HEADER[i][j],
                                    state.liquids[p_idx].phis()[SPECIES.index(i)],
                                )
                                for i in SPECIES
                            ]
                        )
                    )
            else:  # more liquid phases than anticipated
                raise NotImplementedError(
                    f"Uncovered thermo state with:"
                    + f"\nLiquid: {state.liquids}\nGas: {state.gas}"
                )
    else:
        raise NotImplementedError(
            f"Uncovered thermo state phase-count {state.phase_count}"
        )

    return out


def _failed_entry() -> dict[str]:
    """Create a row-entry for failed flashes."""
    failed: dict = _init_empty_results()
    for k in failed.keys():
        failed[k] = NAN_ENTRY
    failed[success_HEADER] = 2
    return failed


def calculate_thermo_pT_data() -> dict[str, list]:
    """Uses thermo to perform the p-T flash for various pressure and temperature ranges.

    Returns a dictionary containing per header (name of some property) respective values
    per p-T point.

    """

    flasher = _thermo_init()
    results = _init_empty_results()

    p_points = np.linspace(P_LIMITS[0], P_LIMITS[1], num=RESOLUTION_pT).tolist()
    T_points = np.linspace(T_LIMITS[0], T_LIMITS[1], num=RESOLUTION_pT).tolist()

    f_num = len(T_points) * len(p_points)
    f_count = 1

    for T in T_points:
        for P in p_points:
            try:
                state = flasher.flash(P=P, T=T, zs=FEED)
            except Exception:
                logger.warn(f"\nThermo p-T-flash failed for p, T = ({P}, {T})\n")
                parsed = _failed_entry()
            else:
                parsed = _thermo_parse_result(state)
                # sanity check
                assert state.P == P, "Thermo p-T result has different pressure."
                assert state.T == T, "Thermo p-T result has different temperature."
                # in the p-T flash, we use the thermo enthalpy also as target enthalpy
                parsed[h_HEADER] = state.H()
            finally:
                parsed[p_HEADER] = P
                parsed[T_HEADER] = T
                for head, val in parsed.items():
                    results[head].append(val)
                print(f"\rFlash: {f_count}/{f_num} done", end="", flush=True)
                logger.info(f"{del_log}Thermo p-T-flash: {f_count}/{f_num}")
                f_count += 1
    logger.info(f"{del_log}Thermo p-T-flash: done\n")

    return results


def _access_shared_objects(
    shared_arrays: list[tuple[Array, Any]], progress_queue: Queue
):
    """Helper function to be called by subprocesses to provide access to shared-memory
    objects.

    ``sharred_arrays`` must be a list of tuples, where the first entry is the
    shared array object and the second entry its data type (as a C-type).

    """
    global arrays_loc, progress_queue_loc
    progress_queue_loc = progress_queue
    arrays_loc = [vec for vec, _ in shared_arrays]


def _array_headers() -> list[str]:
    """Returns a list of header (names) for arrays created for the parallel flash."""
    headers = [
        success_HEADER,
        num_iter_HEADER,
        conditioning_HEADER,
        p_HEADER,
        T_HEADER,
        h_HEADER,
        v_HEADER,
        gas_satur_HEADER,
        gas_frac_HEADER,
        compressibility_HEADER[PHASES[0]],
        compressibility_HEADER[PHASES[1]],
    ]
    for i in SPECIES:
        for j in PHASES[:2]:
            headers += [composition_HEADER[i][j]]
    for i in SPECIES:
        for j in PHASES[:2]:
            headers += [fugacity_HEADER[i][j]]
    return headers


def _create_shared_arrays(size: int) -> list[tuple[Array, Any]]:
    """Creates shared memory arrays for the parallelized flash and returns a list of
    tuples with arrays and their data types as entries.

    Important:
        The order here in the list determines for which quantities they are used.
        The same order is assumed in the parallelized flash.
        It must not be messed with.

        The order corresponds to the order returned by ``get_result_headers``.

    ``size`` determines the size of the allocated arrays. It must be equal the number
    of flashes performed in parallel.

    """
    shared_arrays: list[tuple[Array, Any]] = list()

    INT_PRECISION = c_uint8
    FLOAT_PRECISION = c_double

    def _double_array():
        return RawArray(typecode_or_type=FLOAT_PRECISION, size_or_initializer=size)

    def _uint_array():
        return RawArray(typecode_or_type=INT_PRECISION, size_or_initializer=size)

    # array to store the success flag
    success = _uint_array()
    shared_arrays.append((success, INT_PRECISION))
    # integer array to store the number of iterations necessary
    num_iter = _uint_array()
    shared_arrays.append((num_iter, INT_PRECISION))
    # array storing the condition number of the array at the beginning (initial guess)
    cond_start = _double_array()
    shared_arrays.append((cond_start, FLOAT_PRECISION))
    # arrays containing pressure, temperature, enthalpies and volume
    p = _double_array()
    shared_arrays.append((p, FLOAT_PRECISION))
    T = _double_array()
    shared_arrays.append((T, FLOAT_PRECISION))
    h = _double_array()
    shared_arrays.append((h, FLOAT_PRECISION))
    v = _double_array()
    shared_arrays.append((v, FLOAT_PRECISION))
    # array containing the vapor fraction
    s = _double_array()
    shared_arrays.append((s, FLOAT_PRECISION))
    y = _double_array()
    shared_arrays.append((y, FLOAT_PRECISION))
    # arrays containing the phase compressibility factors
    for _ in range(2):
        Z = _double_array()
        shared_arrays.append((Z, FLOAT_PRECISION))
    # arrays containing the phase composition
    for _ in SPECIES:
        for _ in PHASES[:2]:
            x = _double_array()
            shared_arrays.append((x, FLOAT_PRECISION))
    # arrays containing the fugacities
    for _ in SPECIES:
        for _ in PHASES[:2]:
            phi = _double_array()
            shared_arrays.append((phi, FLOAT_PRECISION))

    return shared_arrays


def _progress_counter(q: Queue, NC: int, flash_result: AsyncResult):
    """A function sharing a Queue object with other processes, which receives
    the index of all finished flashes. This function finishes when all indices
    where received."""
    progress_array = Array(typecode_or_type=c_uint8, size_or_initializer=NC)

    while True:
        i = q.get()
        progress_array[i] = 1
        progress = int(sum(progress_array))
        logger.info(f"{del_log}Parallel flash: {progress}/{NC}")
        if progress == NC:
            break


def create_mixture(
    num_vals: int,
    flash_type: str,
) -> tuple[pp.composite.NonReactiveMixture, pp.composite.FlashNR]:
    """Returns instances of the modelled mixture and flash using PorePy's framework.

    ``num_vals`` is an integer indicating how many DOFs per state function are set.
    This is used for vectorization.
    Especially, choose 1 for a point-wise and parallelized flash.

    ``flash_type`` is a string containing the flash type in terms of specificiations.
    This influences the solver settings.

    Configure flash parameters here.

    """

    species = pp.composite.load_species(SPECIES)

    comps = [
        pp.composite.peng_robinson.H2O.from_species(species[0]),
        pp.composite.peng_robinson.CO2.from_species(species[1]),
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

    mix.set_up(num_vals=num_vals)

    # instantiating Flasher, without auxiliary variables V and W
    flash = pp.composite.FlashNR(mix)
    flash.use_armijo = True
    flash.armijo_parameters["rho"] = 0.99
    flash.armijo_parameters["j_max"] = 70
    flash.armijo_parameters["return_max"] = True
    flash.newton_update_chop = 1.0
    flash.tolerance = 1e-5
    flash.max_iter = 150

    if flash_type == "h-v":
        flash.armijo_parameters["rho"] = 0.9
        flash.armijo_parameters["j_max"] = 150

    return mix, flash


def _porepy_parse_state(state: pp.composite.ThermodynamicState) -> dict:
    """Function to parse the resulting state after a porepy flash into a structure
    ready for writing to csv.

    Only meant for states with 1 value per state function.

    Parses only fractional variables and phase split.

    """
    out = _init_empty_results()
    for k in out.keys():
        out[k] = NAN_ENTRY

    y = state.y[1][0]
    if y >= 1:
        out[phases_HEADER] = "G"
    elif y <= 0:
        out[phases_HEADER] = "L"
    else:
        out[phases_HEADER] = "GL"
    out[gas_frac_HEADER] = y
    out[liq_frac_HEADER[0]] = 1 - y

    s = state.s[1][0]
    out[gas_satur_HEADER] = s
    out[liq_satur_HEADER[0]] = 1 - s

    # liquid phase composition
    for i, s in enumerate(SPECIES):
        x_ij = state.X[0][i][0]
        out[composition_HEADER[s][PHASES[1]]] = x_ij
    # gas phase composition
    for i, s in enumerate(SPECIES):
        x_ij = state.X[1][i][0]
        out[composition_HEADER[s][PHASES[0]]] = x_ij

    return out


def _parallel_porepy_flash(args):
    """Performs a flash (including modelling) and stores the results in shared
    memory.

    ``args`` must be a tuple containing the index where the results should be stored,
    the defined state points, flash-type string and quickshot bool.

    Warning:
        There are some unresolved issues with parallel subprocesses if
        numpy/scipy/pypardiso throw errors or warnings. It causes the respective
        subprocess unable to join, despite finishing all flashes.

    """

    i, state_1, state_2, flash_type, quickshot = args
    msg = (i, state_1, state_2)

    # accessing shared memory
    global arrays_loc, progress_queue_loc
    (
        success_arr,
        num_iter_arr,
        cond_arr,
        p_arr,
        T_arr,
        h_arr,
        v_arr,
        s_arr,
        y_arr,
        Z_G_arr,
        Z_L_arr,
        x_h2o_G_arr,
        x_h2o_L_arr,
        x_co2_G_arr,
        x_co2_L_arr,
        phi_h2o_G_arr,
        phi_h2o_L_arr,
        phi_co2_G_arr,
        phi_co2_L_arr,
    ) = arrays_loc

    mix, flash = create_mixture(1, flash_type)
    feed = [np.ones(1) * z for z in FEED]

    # Default entries are FAILURE
    success_arr[i] = 2
    num_iter_arr[i] = 0
    cond_arr[i] = NAN_ENTRY
    p_arr[i] = NAN_ENTRY
    T_arr[i] = NAN_ENTRY
    h_arr[i] = NAN_ENTRY
    v_arr[i] = NAN_ENTRY
    s_arr[i] = NAN_ENTRY
    y_arr[i] = NAN_ENTRY
    Z_L_arr[i] = NAN_ENTRY
    Z_G_arr[i] = NAN_ENTRY
    x_h2o_G_arr[i] = NAN_ENTRY
    x_h2o_L_arr[i] = NAN_ENTRY
    x_co2_G_arr[i] = NAN_ENTRY
    x_co2_L_arr[i] = NAN_ENTRY
    phi_h2o_G_arr[i] = NAN_ENTRY
    phi_h2o_L_arr[i] = NAN_ENTRY
    phi_co2_G_arr[i] = NAN_ENTRY
    phi_co2_L_arr[i] = NAN_ENTRY

    if flash_type == "p-T":
        state_input = {"p": np.array([state_1]), "T": np.array([state_2])}
    elif flash_type == "p-h":
        state_input = {"p": np.array([state_1]), "h": np.array([state_2])}
    elif flash_type == "h-v":
        state_input = {"h": np.array([state_1]), "v": np.array([state_2])}

    try:
        success_, state = flash.flash(
            state=state_input,
            feed=feed,
            eos_kwargs={"apply_smoother": True},
            quickshot=quickshot,
            return_system=True,
        )
    except Exception as err:  # if Flasher fails, flag as failed
        logger.warn(f"\nParallel {flash_type} flash crashed at {msg}\n{str(err)}\n")
    else:
        success_arr[i] = success_
        if success_ == 2:
            logger.warn(f"\nParallel {flash_type} diverged at {msg}\n")
        else:
            if success_ == 1:
                logger.warn(
                    f"\nParallel {flash_type} stopped after max iter at {msg}\n"
                )
            try:
                cn = np.linalg.cond(state(with_derivatives=True).jac.todense())
            except:
                logger.warn(
                    f"\nParallel {flash_type} failed to compute condition number at "
                    + f"{msg} (exit code = {success_})\n"
                )
                cn = NAN_ENTRY

            cond_arr[i] = cn
            if quickshot:
                num_iter_arr[i] = 0
            else:
                num_iter_arr[i] = flash.history[-1]["iterations"]

            state = state.export_state()

            p_arr[i] = state.p[0]
            T_arr[i] = state.T[0]
            h_arr[i] = state.h[0]
            v_arr[i] = state.v[0]

            s_arr[i] = state.s[1][0]
            y_arr[i] = state.y[1][0]
            x_h2o_L_arr[i] = state.X[0][0][0]
            x_h2o_G_arr[i] = state.X[1][0][0]
            x_co2_L_arr[i] = state.X[0][1][0]
            x_co2_G_arr[i] = state.X[1][1][0]
            props = mix.compute_properties(state.p, state.T, state.X, store=False)
            Z_L_arr[i] = props[0].Z[0]
            Z_G_arr[i] = props[1].Z[0]
            phi_h2o_L_arr[i] = props[0].phis[0][0]
            phi_co2_L_arr[i] = props[0].phis[1][0]
            phi_h2o_G_arr[i] = props[1].phis[0][0]
            phi_co2_G_arr[i] = props[1].phis[1][0]

    # to ensure proper mapping between state args (just in case something goes wrong)
    if flash_type == "p-T":
        p_arr[i] = state_1
        T_arr[i] = state_2
    elif flash_type == "p-h":
        p_arr[i] = state_1
        h_arr[i] = state_2
    elif flash_type == "h-v":
        h_arr[i] = state_1
        v_arr[i] = state_2

    progress_queue_loc.put(i, block=False)


def calculate_porepy_data(
    state_1: list[float], state_2: list[float], flash_type: str, quickshot: bool = False
) -> dict:
    """Performs the PorePy flash for given pressure-temperature points and
    returns a result structure similar to that of the thermo computation.

    If ``quickshot`` is True, returns the results from the initial guess."""

    results = _init_empty_results()
    nf = len(state_1)

    if CALCULATION_MODE == 1:  # point-wise flash
        v = np.ones(1)
        logger.info(
            f"PorePy {flash_type}-flash: initializing point-wise calculations .."
        )
        mix, flash = create_mixture(1, flash_type)
        feed = [v * z for z in FEED]

        for f, xy in enumerate(zip(state_1, state_2)):
            if flash_type == "p-T":
                state_input = {"p": np.array([xy[0]]), "T": np.array([xy[1]])}
            elif flash_type == "p-h":
                state_input = {"p": np.array([xy[0]]), "h": np.array([xy[1]])}
            elif flash_type == "h-v":
                state_input = {"h": np.array([xy[0]]), "v": np.array([xy[1]])}

            try:
                success, state = flash.flash(
                    state=state_input,
                    feed=feed,
                    eos_kwargs={"apply_smoother": True},
                    quickshot=quickshot,
                    return_system=True,
                )
            except Exception as err:
                logger.warn(
                    f"\nPorePy {flash_type} flash crashed at ({f}, {xy})\n{str(err)}\n"
                )
                res = _failed_entry()
            else:
                if success == 2:
                    logger.warn(
                        f"\nPorePy {flash_type} flash diverged at ({f}, {xy})\n"
                    )
                else:
                    if success == 1:
                        logger.warn(
                            f"\nPorePy {flash_type} stopped after max iter at ({f}, {xy})\n"
                        )

                    try:
                        cn = np.linalg.cond(state(with_derivatives=True).jac.todense())
                    except Exception:
                        logger.warn(
                            f"\nPorepy {flash_type} failed to compute condition number"
                            + f" at ({f}, {xy}) (exit code = {success})\n"
                        )
                        cn = NAN_ENTRY
                    else:
                        cn = float(cn)

                    state = state.export_state()
                    res = _porepy_parse_state(state)

                    res[success_HEADER] = success
                    res[conditioning_HEADER] = cn

                    if quickshot:
                        res[num_iter_HEADER] = 0
                    else:
                        res[num_iter_HEADER] = int(flash.history[-1]["iterations"])

                    res[p_HEADER] = state.p[0]
                    res[T_HEADER] = state.T[0]
                    res[h_HEADER] = state.h[0]
                    res[v_HEADER] = state.v[0]

                    props = mix.compute_properties(
                        state.p, state.T, state.X, store=False
                    )

                    res[compressibility_HEADER[PHASES[1]]] = props[0].Z[0]
                    for i, s in enumerate(SPECIES):
                        res[fugacity_HEADER[s][PHASES[1]]] = props[0].phis[i][0]
                    res[compressibility_HEADER[PHASES[0]]] = props[1].Z[0]
                    for i, s in enumerate(SPECIES):
                        res[fugacity_HEADER[s][PHASES[0]]] = props[1].phis[i][0]

            # to ensure proper mapping between state args
            if flash_type == "p-T":
                res[p_HEADER] = xy[0]
                res[T_HEADER] = xy[1]
            elif flash_type == "p-h":
                res[p_HEADER] = xy[0]
                res[h_HEADER] = xy[1]
            elif flash_type == "h-v":
                res[h_HEADER] = xy[0]
                res[v_HEADER] = xy[1]

            for key, val in res.items():
                results[key].append(val)

            logger.info(f"{del_log}PorePy {flash_type} flash: {f+1} / {nf} ..")

    elif CALCULATION_MODE == 2:  # vectorized flash
        pass
    elif CALCULATION_MODE == 3:  # parallelized flash

        args = [
            (i, x, y, flash_type, quickshot)
            for i, x, y in zip(np.arange(nf), state_1, state_2)
        ]
        shared_arrays = _create_shared_arrays(nf)
        logger.info(f"Parallel {flash_type} flash: starting ..")
        start_time = time.time()
        prog_q = Queue(maxsize=nf)
        with Pool(
            processes=NUM_PHYS_CPU_CORS + 1,
            initargs=(shared_arrays, prog_q),
            initializer=_access_shared_objects,
        ) as pool:

            prog_process = Process(
                target=_progress_counter, args=(prog_q, nf, None), daemon=True
            )
            prog_process.start()

            chunksize = np.array(
                [NUM_PHYS_CPU_CORS, RESOLUTION_hv, RESOLUTION_ph, RESOLUTION_pT]
            ).min()
            result = pool.map_async(_parallel_porepy_flash, args, chunksize=chunksize)

            # Wait for some time and see if processes terminate as they should
            # we terminate if the processes for some case could not finish
            result.wait(60 * 60 * 5)
            if result.ready():
                prog_process.join(5)
                if prog_process.exitcode != 0:
                    prog_process.terminate()
                pool.close()
            else:
                prog_process.terminate()
                logger.warn(f"\nParallel {flash_type} flash: terminated\n")
                pool.close()
                pool.terminate()
            pool.join()

        end_time = time.time()
        logger.info(
            f"\nParallel {flash_type} flash: finished after {end_time - start_time} seconds.\n"
        )

        result_vecs = [
            list(np.frombuffer(vec, dtype=dtype))
            # list(np.frombuffer(vec.get_obj(), dtype=dtype))  # For Array (synchronized)
            for vec, dtype in shared_arrays
        ]
        results = dict(
            [(header, vec) for header, vec in zip(_array_headers(), result_vecs)]
        )
    else:
        raise ValueError(f"Unknown flash calculation mode {CALCULATION_MODE}.")

    return results


def plot_crit_point_H2O(axis: plt.Axes):
    """Plot critical pressure and temperature in p-T plot for components H2O and CO2."""

    S = pp.composite.load_species(SPECIES)

    img = [
        axis.plot(
            s.T_crit,
            s.p_crit * PRESSURE_SCALE,
            "*",
            markersize=MARKER_SIZE,
            color="red",
        )[0]
        for s in S[:1]
    ]

    return img, [f"crit. point {s.name}" for s in S[:1]]


def plot_max_iter_reached(
    axis: plt.Axes,
    p: np.ndarray,
    T: np.ndarray,
    max_iter_reached: np.ndarray,
) -> figure.Figure:
    """Plots markers where the maximal number of iterations is reached."""
    if np.any(max_iter_reached):
        img = axis.plot(
            T[max_iter_reached],
            p[max_iter_reached] * PRESSURE_SCALE,
            "P",
            markersize=MARKER_SIZE,
            color="black",
        )
        return [img[0]], ["max iter reached"]
    else:
        return [], []


def plot_phase_split_pT(
    axis: plt.Axes,
    p: np.ndarray,
    T: np.ndarray,
    split: np.ndarray,
) -> figure.Figure:
    """Plots a phase split figure across a range of pressure and temperature values."""

    # cmap = mpl.colors.ListedColormap(
    #     ["firebrick", "royalblue", "mediumturquoise", "forestgreen"]
    # )
    cmap = mpl.colors.ListedColormap(np.array([NA_COL, LIQ_COL, MPHASE_COL, GAS_COL]))
    img = axis.pcolormesh(
        T,
        p * PRESSURE_SCALE,
        split,
        cmap=cmap,
        vmin=0,
        vmax=3,
        shading="nearest",  # gouraud
    )

    return img


def plot_abs_error_pT(
    axis: plt.Axes,
    p: np.ndarray,
    T: np.ndarray,
    error: np.ndarray,
    norm=None,
) -> figure.Figure:
    """Plots the absolute error in grey scales."""

    if norm:
        kwargs = {"norm": norm}
    else:
        kwargs = {"vmin": error.min(), "vmax": error.max()}

    img = axis.pcolormesh(
        T, p * PRESSURE_SCALE, error, cmap="Greys", shading="nearest", **kwargs
    )

    return img


def _plot_critical_line(axis: plt.Axes, A_mesh: np.ndarray):
    A_CRIT = pp.composite.peng_robinson.PengRobinsonEoS.A_CRIT
    B_CRIT = pp.composite.peng_robinson.PengRobinsonEoS.B_CRIT
    slope = B_CRIT / A_CRIT
    x_vals = np.sort(np.unique(A_mesh.flatten()))
    x_vals = x_vals[x_vals <= A_CRIT]
    y_vals = 0.0 + slope * x_vals
    # critical line
    img_line = axis.plot(x_vals, y_vals, "-", color="black", linewidth=3)
    # critical point
    img_point = axis.plot(A_CRIT, B_CRIT, "*", markersize=MARKER_SIZE, color="red")
    return [img_point[0], img_line[0]], ["(A_c, B_c)", "crit. line"]


def _plot_Widom_line(axis: plt.Axes, A_mesh: np.ndarray, B_mesh: np.ndarray):
    """Plots the approximation of the Widom-line."""
    A_CRIT = pp.composite.peng_robinson.PengRobinsonEoS.A_CRIT
    B_CRIT = pp.composite.peng_robinson.PengRobinsonEoS.B_CRIT
    x_vals = np.sort(np.unique(A_mesh.flatten()))
    x_vals = x_vals[x_vals >= A_CRIT]
    y_vals = pp.composite.peng_robinson.PengRobinsonEoS.Widom_line(x_vals)
    cap = y_vals <= B_mesh.max()
    y_vals = y_vals[cap]
    x_vals = x_vals[cap]

    # Widom line
    img_line = axis.plot(x_vals, y_vals, linestyle="dashed", color="black", linewidth=3)
    # subcrit- triangle
    img_b = axis.plot(
        [A_CRIT, A_mesh.max()],
        [B_CRIT, B_CRIT],
        linestyle="dotted",
        color="black",
        linewidth=3,
    )

    return [img_line[0], img_b[0]], ["Widom line", "B=B_c"]


def plot_root_regions(
    axis: plt.Axes,
    A_mesh: np.ndarray,
    B_mesh: np.ndarray,
    regions: np.ndarray,
    liq_root: np.ndarray,
):
    """A discrete plot for plotting the root cases."""
    # cmap = mpl.colors.ListedColormap(["yellow", "green", "blue", "indigo"])
    cmap = mpl.colors.ListedColormap(
        np.array([GREY_COL, WHITE_COL, NA_COL, MPHASE_COL])
    )
    img = axis.pcolormesh(
        A_mesh,
        B_mesh,
        regions,
        cmap=cmap,
        vmin=0,
        vmax=3,
        shading="nearest",
    )
    imgs_c, legs_c = _plot_critical_line(axis, A_mesh)

    violated = (liq_root <= B_mesh) & (
        B_mesh >= pp.composite.peng_robinson.PengRobinsonEoS.critical_line(A_mesh)
    )
    if np.any(violated):
        mr = np.ma.array(regions, mask=np.logical_not(violated))
        hatch = axis.pcolor(
            A_mesh,
            B_mesh,
            mr,
            hatch="//",
            edgecolor="black",
            cmap=mpl.colors.ListedColormap(["none"]),
            facecolor="none",
            vmin=0,
            vmax=3,
            shading="nearest",
            lw=0,
            zorder=2,
        )
        img_v = [hatch]
        leg_v = [f"Z_L <= B"]
    else:
        img_v = []
        leg_v = []

    axis.legend(
        imgs_c + img_v,
        legs_c + leg_v,
        loc="upper right",
        markerscale=MARKER_SCALE,
    )

    return img


def plot_root_extensions(
    axis: plt.Axes,
    A_mesh: np.ndarray,
    B_mesh: np.ndarray,
    root_extensions: np.ndarray,
):
    """A discrete plot for plotting the root cases."""
    # cmap = mpl.colors.ListedColormap(["white", "royalblue", "orange", "forestgreen"])
    cmap = mpl.colors.ListedColormap(
        np.array([MPHASE_COL, LIQ_COL, GAS_COL_2, GAS_COL])
    )
    img = axis.pcolormesh(
        A_mesh,
        B_mesh,
        root_extensions,
        cmap=cmap,
        vmin=0,
        vmax=3,
        shading="nearest",
    )

    img_w, leg_w = _plot_Widom_line(axis, A_mesh, B_mesh)
    imgs_c, legs_c = _plot_critical_line(axis, A_mesh)

    axis.legend(
        imgs_c + img_w, legs_c + leg_w, loc="upper left", markerscale=MARKER_SCALE
    )

    return img


def plot_Widom_points_experimental(axis: plt.Axes):
    """Plots the three points corresponding to the experimental Widom line
    (Maxim et al. 2019)"""

    img = axis.plot(
        WIDOM_LINE[1],
        WIDOM_LINE[0] * PRESSURE_SCALE,
        "D-",
        markersize=MARKER_SIZE,
        color="black",
    )
    return [img[0]], ["Widom-line data"]


def plot_hv_iso(
    axis: plt.Axes,
    x: np.ndarray,
    p_err: np.ndarray,
    T_err: np.ndarray,
    s_err: np.ndarray,
    y_err: np.ndarray,
):
    """Plots the pressure, temperature, saturation and molar fraction error after the
    h-v flash."""
    marker_size = int(np.floor(MARKER_SIZE / 2))
    marker_size = MARKER_SIZE
    img_p = axis.plot(
        x, p_err, "--o", fillstyle="none", color="red", markersize=marker_size
    )[0]
    img_s = axis.plot(
        x, s_err, "--P", fillstyle="none", color="black", markersize=marker_size
    )[0]
    img_T = axis.plot(x, T_err, "-s", color="red", markersize=marker_size)[0]
    img_y = axis.plot(x, y_err, "-D", color="black", markersize=marker_size)[0]

    return [img_p, img_s, img_T, img_y], ["p err", "s err", "T err", "y err"]
