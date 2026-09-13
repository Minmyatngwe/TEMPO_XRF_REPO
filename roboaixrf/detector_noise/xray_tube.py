from __future__ import annotations

from typing import Dict, List

import numpy as np
import spekpy as sp

from pydantic import validate_call


@validate_call
def get_flu(
    voltage: float,
    anode_degree: float,
    anode_target_material: str,
    filters: List[Dict],
    source_to_tube_collimator_mm: float,
    tube_type: str,
    target_thickness_um: float = 0.0,
    mas: float = 1.0,) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Build a SpekPy tube spectrum and return:

    1. energy bins in keV
    2. spectrum values used as relative Geant4 GPS weights
    3. total physical fluence at the requested mAs in photons/cm²

    Notes
    -----
    The Geant4 source shape is normally generated with mas=1.
    For an actual detector acquisition, call this function again with:

        mas = current_mA * live_time_s

    and use the third returned value for physical photon scaling.
    """

    if voltage <= 0:
        raise ValueError("voltage must be greater than 0 kV.")

    if source_to_tube_collimator_mm <= 0:
        raise ValueError(
            "source_to_tube_collimator_mm must be greater than 0."
        )

    if mas <= 0:
        raise ValueError("mas must be greater than 0.")

    if tube_type == "reflection":
        spectrum = sp.Spek(
            kvp=voltage,
            th=anode_degree,
            targ=anode_target_material,
            physics="kqp",
        )

    elif tube_type == "transmission":
        if target_thickness_um <= 0:
            raise ValueError(
                "target_thickness_um must be greater than 0 "
                "for a transmission tube."
            )

        spectrum = sp.Spek(
            kvp=voltage,
            th=anode_degree,
            targ=anode_target_material,
            physics="kqp",
            trans=True,
            thick=target_thickness_um,
        )

    else:
        raise ValueError(
            "Unsupported tube type. "
            f"Expected 'reflection' or 'transmission', got {tube_type!r}."
        )

    for filter_config in filters:
        spectrum.filter(
            filter_config["element"],
            filter_config["thickness_mm"],
        )

    distance_cm = (source_to_tube_collimator_mm / 10.0)

    # We deliberately keep this at 1 mAs because the normalized spectral
    # shape does not depend on current/time. This makes compile() stable.
    energy_bin_kev, fluence_list = spectrum.get_spectrum(
        z=distance_cm,
        diff=False,
    )

    total_fluence_photons_cm2 = spectrum.get_flu(
        z=distance_cm,
        mas=mas,
    )

    energy_bin_kev = np.asarray(
        energy_bin_kev,
        dtype=np.float64,
    )

    fluence_list = np.asarray(
        fluence_list,
        dtype=np.float64,
    )

    if energy_bin_kev.size == 0:
        raise ValueError(
            "SpekPy returned an empty energy spectrum."
        )

    if fluence_list.size != energy_bin_kev.size:
        raise ValueError(
            "SpekPy energy and fluence arrays have different lengths."
        )

    if not np.all(np.isfinite(fluence_list)):
        raise ValueError(
            "SpekPy returned non-finite spectrum values."
        )

    if np.sum(fluence_list) <= 0:
        raise ValueError(
            "SpekPy returned zero total spectrum weight."
        )

    if not np.isfinite(total_fluence_photons_cm2):
        raise ValueError(
            "SpekPy returned a non-finite total fluence."
        )

    if total_fluence_photons_cm2 <= 0:
        raise ValueError(
            "SpekPy returned zero total fluence."
        )

    return (
        energy_bin_kev,
        fluence_list,
        float(total_fluence_photons_cm2),
    )
