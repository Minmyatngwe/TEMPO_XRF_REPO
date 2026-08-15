import json
import shutil
from pathlib import Path

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import uproot

from detector_noise.pipeline import (
    apply_detectornoise,
    save_file,
)


# =========================================================================
# FIND COMPLETED SIMULATION
# =========================================================================

run_info = st.session_state.get(
    "simulation_run"
)


# -------------------------------------------------------------------------
# If a simulation is currently running, detector noise cannot be applied yet.
# -------------------------------------------------------------------------

if run_info:

    process = run_info.get(
        "process"
    )

    if process is not None:

        try:
            simulation_running = (
                process.poll() is None
            )

        except Exception:
            simulation_running = False

    else:
        simulation_running = False

else:
    simulation_running = False


if simulation_running:

    st.info(
        f"Simulation '{run_info['file_name']}' is still running. "
        "Wait until it finishes before applying detector noise."
    )

    st.stop()


# =========================================================================
# GET COMPLETED RUN INFORMATION
# =========================================================================

simulation_ready = st.session_state.get(
    "simulation_status",
    False,
)


if not simulation_ready:

    st.info(
        "Run a simulation first."
    )

    st.stop()


# =========================================================================
# ROOT FILE
# =========================================================================

root_file_path_value = st.session_state.get(
    "root_file_path"
)


if not root_file_path_value:

    st.error(
        "The completed simulation ROOT file path is missing."
    )

    st.stop()


root_file_path = Path(
    root_file_path_value
).resolve()


if not root_file_path.exists():

    st.error(
        "The simulation ROOT file does not exist:\n\n"
        f"{root_file_path}"
    )

    st.stop()


# =========================================================================
# UPDATED CONFIG
#
# NO UPLOAD.
#
# First use the path saved by simulation.py.
# If unavailable, find updated_config.json beside the ROOT file.
# =========================================================================

updated_json_path_value = (
    st.session_state.get(
        "simulation_updated_config_path"
    )
)


if updated_json_path_value:

    updated_json_path = Path(
        updated_json_path_value
    ).resolve()

else:

    updated_json_path = (
        root_file_path.parent
        / "updated_config.json"
    ).resolve()


if not updated_json_path.exists():

    st.error(
        "updated_config.json could not be found for this simulation:\n\n"
        f"{updated_json_path}"
    )

    st.stop()


# =========================================================================
# LOAD UPDATED CONFIG AUTOMATICALLY
# =========================================================================

try:

    with updated_json_path.open(
        "r",
        encoding="utf-8",
    ) as f:

        simulation_config = json.load(
            f
        )

except Exception as exc:

    st.error(
        "Could not read updated_config.json: "
        f"{exc}"
    )

    st.stop()


# =========================================================================
# GET SIMULATION VALUES
# =========================================================================

simulation_info = simulation_config.get(
    "simulation",
    {},
)


# -------------------------------------------------------------------------
# Prefer information from updated_config.json.
#
# Fall back to session state for compatibility.
# -------------------------------------------------------------------------

one_second_photon = float(
    simulation_info.get(
        "one_second_photon",
        st.session_state.get(
            "one_second_photon",
            0.0,
        ),
    )
)


area_on_sample = float(
    simulation_info.get(
        "beam_area_cm2",
        st.session_state.get(
            "area_on_sample",
            0.0,
        ),
    )
)


beamon = int(
    simulation_info.get(
        "beam_on_events",
        st.session_state.get(
            "beamon",
            0,
        ),
    )
)


voltage = float(
    st.session_state.get(
        "voltage",
        0.0,
    )
)


# =========================================================================
# VALIDATE VALUES
# =========================================================================

if one_second_photon <= 0:

    st.error(
        "Invalid one_second_photon value in the simulation."
    )

    st.stop()


if area_on_sample <= 0:

    st.error(
        "Invalid beam area in the simulation."
    )

    st.stop()


if beamon <= 0:

    st.error(
        "Invalid beam-on event count."
    )

    st.stop()


# =========================================================================
# CHECK ROOT TREE
# =========================================================================

try:

    root_file = uproot.open(
        root_file_path
    )

    if "MyTree" not in root_file:

        st.error(
            "MyTree was not found in the ROOT file."
        )

        st.stop()

    tree = root_file[
        "MyTree"
    ]

except Exception as exc:

    st.error(
        f"Could not open ROOT file: {exc}"
    )

    st.stop()


# =========================================================================
# PAGE
# =========================================================================

st.title(
    "Detector Response"
)


# =========================================================================
# RUN SUMMARY
# =========================================================================

run_name = simulation_info.get(
    "file_name",
    root_file_path.stem,
)


with st.expander(
    "Simulation information",
    expanded=False,
):

    st.write(
        "Run:",
        run_name,
    )

    st.write(
        "ROOT file:",
        root_file_path.name,
    )

    st.write(
        "Beam-on events:",
        f"{beamon:,}",
    )

    st.write(
        "Tube voltage:",
        f"{voltage:g} kV",
    )

    st.write(
        "One-second photon fluence:",
        one_second_photon,
    )

    st.write(
        "Beam area on sample:",
        f"{area_on_sample:.8f} cm²",
    )

    st.write(
        "ROOT entries:",
        tree.num_entries,
    )


# =========================================================================
# DETECTOR PARAMETERS
# =========================================================================

st.subheader(
    "Detector parameters"
)


col1, col2 = st.columns(
    2
)


with col1:

    fwhm = st.number_input(
        "FWHM (eV)",
        min_value=0.0,
        key="detector_noise_fwhm",
        format="%.5f",
    )


    fwhm_energy = st.number_input(
        "FWHM at energy (keV)",
        min_value=0.0,
        key="detector_noise_fwhm_energy",
        format="%.5f",
    )


    fano_factor = st.number_input(
        "Fano factor",
        min_value=0.0,
        value=0.115,
        key="detector_noise_fano_factor",
        format="%.5f",
    )


    pair_creation = st.number_input(
        "Pair creation energy (eV)",
        min_value=0.0,
        value=3.6,
        key="detector_noise_paircreation_energy",
        format="%.5f",
    )


    mca_channels = int(
        st.number_input(
            "Number of MCA channels",
            min_value=1,
            value=2048,
            step=1,
            key="detector_noise_mca",
        )
    )


with col2:

    live_time = st.number_input(
        "Live time (s)",
        min_value=0.0,
        key="detector_noise_live_time",
        format="%.5f",
    )


    detector_zero_offset = st.number_input(
        "Detector zero offset (keV)",
        key="detector_zero_offset",
        step=0.000001,
        format="%.6f",
    )


    detector_gain = st.number_input(
        "Detector gain (keV/channel)",
        min_value=0.0,
        key="detector_gain_v2",
        step=0.000001,
        format="%.6f",
    )


    pile_up_window_us = st.number_input(
        "Pile-up window (µs)",
        min_value=0.0,
        value=0.1,
        key="detector_noise_pile_up_window_us",
        format="%.5f",
    )


# =========================================================================
# EXPECTED PHOTONS
# =========================================================================

total_photon = (
    one_second_photon
    * area_on_sample
    * live_time
)


st.divider()


summary_col1, summary_col2, summary_col3 = st.columns(
    3
)


summary_col1.metric(
    "Beam area",
    f"{area_on_sample:.6f} cm²",
)


summary_col2.metric(
    "Live time",
    f"{live_time:g} s",
)


summary_col3.metric(
    "Expected photons",
    f"{total_photon:,.0f}",
)


# =========================================================================
# APPLY DETECTOR NOISE
# =========================================================================

apply_noise = st.button(
    "Apply detector noise",
    type="primary",
    use_container_width=True,
)


if apply_noise:

    # ---------------------------------------------------------------------
    # Validate detector settings
    # ---------------------------------------------------------------------

    if live_time <= 0:

        st.error(
            "Live time must be greater than zero."
        )

        st.stop()


    if fwhm <= 0:

        st.error(
            "FWHM must be greater than zero."
        )

        st.stop()


    if fwhm_energy <= 0:

        st.error(
            "FWHM reference energy must be greater than zero."
        )

        st.stop()


    if detector_gain <= 0:

        st.error(
            "Detector gain must be greater than zero."
        )

        st.stop()


    # =====================================================================
    # SAVE DETECTOR SETTINGS INTO updated_config.json
    # =====================================================================

    simulation_config[
        "detector_noise"
    ] = {

        "live_time":
            float(
                live_time
            ),

        "fwhm":
            float(
                fwhm
            ),

        "fwhm_energy":
            float(
                fwhm_energy
            ),

        "fano_factor":
            float(
                fano_factor
            ),

        "pair_creation":
            float(
                pair_creation
            ),

        "mca_channels":
            int(
                mca_channels
            ),

        "pile_up_window_us":
            float(
                pile_up_window_us
            ),

        "detector_zero_offset_kev":
            float(
                detector_zero_offset
            ),

        "detector_gain_kev":
            float(
                detector_gain
            ),
    }


    # =====================================================================
    # RUN DETECTOR RESPONSE
    # =====================================================================

    with st.spinner(
        "Applying detector response..."
    ):

        try:

            (
                scaled_count,
                energy_center,
                original_scaled_count,
                average_channel_wise_yield,
                se_channel_wise_yield,
                spectrum_yield_avg,
                spectrum_se,
            ) = apply_detectornoise(

                root_path=str(
                    root_file_path
                ),

                beam_on=beamon,

                number_of_photon=(
                    total_photon
                ),

                fwhm=fwhm,

                fwhm_energy=(
                    fwhm_energy
                ),

                fano_factor=(
                    fano_factor
                ),

                pair_creation_energy_ev=(
                    pair_creation
                ),

                mca_channels=(
                    mca_channels
                ),

                live_time=(
                    live_time
                ),

                pile_up_window=(
                    pile_up_window_us
                ),

                detector_zero_offset=(
                    detector_zero_offset
                ),

                detector_gain=(
                    detector_gain
                ),
            )

        except Exception as exc:

            st.error(
                "Detector-noise processing failed:\n\n"
                f"{exc}"
            )

            st.stop()


    # =====================================================================
    # SAVE UNCERTAINTY INTO JSON
    # =====================================================================

    simulation_config[
        "detector_noise"
    ][
        "se_detector_yield"
    ] = (
        np.asarray(
            se_channel_wise_yield
        ).tolist()
    )


    try:

        with updated_json_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                simulation_config,
                f,
                indent=4,
                ensure_ascii=False,
            )

    except Exception as exc:

        st.error(
            "Detector response was calculated, "
            "but updated_config.json could not be saved: "
            f"{exc}"
        )


    # =====================================================================
    # RESULTS
    # =====================================================================

    st.success(
        "Detector response completed."
    )


    st.write(
        "Total photons:",
        f"{total_photon:,.0f}",
    )


    st.write(
        "One-second photon fluence:",
        one_second_photon,
    )


    # =====================================================================
    # PEAK AREA
    # =====================================================================

    mask = (
        (energy_center > 6.125)
        & (energy_center < 6.775)
    )


    total_scaled_counts = np.sum(
        scaled_count
    )


    if total_scaled_counts > 0:

        area_of_peak = (
            np.sum(
                scaled_count[
                    mask
                ]
            )
            / total_scaled_counts
        )

    else:

        area_of_peak = 0.0


    print(
        "area_of_peak",
        area_of_peak,
    )

    print(
        "sim peak",
        scaled_count[
            mask
        ].sum(),
    )

    print(
        "sim outside",
        scaled_count[
            ~mask
        ].sum(),
    )


    # =====================================================================
    # UNCERTAINTY VALUES
    # =====================================================================

    count_uncertainty = (
        spectrum_se
        * total_photon
    )


    expected_count = (
        spectrum_yield_avg
        * total_photon
    )


    se_channel_wise_yield_scaled = (
        se_channel_wise_yield
        * total_photon
    )


    if spectrum_yield_avg != 0:

        relative_uncertainty_percent = (
            spectrum_se
            / spectrum_yield_avg
        ) * 100

    else:

        relative_uncertainty_percent = (
            0.0
        )


    # =====================================================================
    # RESULT SUMMARY
    # =====================================================================

    result_col1, result_col2, result_col3 = st.columns(
        3
    )


    result_col1.metric(
        "Expected counts",
        f"{expected_count:,.0f}",
    )


    result_col2.metric(
        "Monte Carlo SE",
        f"{count_uncertainty:,.0f}",
    )


    result_col3.metric(
        "Relative uncertainty",
        f"{relative_uncertainty_percent:.5f}%",
    )


    # =====================================================================
    # PLOTS
    # =====================================================================

    plot_col1, plot_col2 = st.columns(
        2
    )


    # ---------------------------------------------------------------------
    # Spectrum after detector noise
    # ---------------------------------------------------------------------

    with plot_col1:

        fig1 = px.line(
            x=energy_center,
            y=scaled_count,
            title=(
                "Spectrum After Adding Detector Noise"
            ),
            labels={
                "x": "Energy (keV)",
                "y": "Scaled count",
            },
        )


        st.plotly_chart(
            fig1,
            key="spectrum_after_noise_chart",
            width="stretch",
        )


        st.caption(
            "Fraction of counts between "
            "6.125–6.775 keV: "
            f"{area_of_peak:.5%}"
        )


    # ---------------------------------------------------------------------
    # Original spectrum + Monte Carlo uncertainty
    # ---------------------------------------------------------------------

    with plot_col2:

        fig2 = go.Figure()


        # Lower uncertainty boundary
        fig2.add_trace(

            go.Scatter(
                x=energy_center,

                y=(
                    original_scaled_count
                    - se_channel_wise_yield_scaled
                ),

                mode="lines",

                line=dict(
                    width=0
                ),

                showlegend=False,
            )
        )


        # Upper boundary and shaded region
        fig2.add_trace(

            go.Scatter(
                x=energy_center,

                y=(
                    original_scaled_count
                    + se_channel_wise_yield_scaled
                ),

                fill="tonexty",

                mode="lines",

                fillcolor=(
                    "rgba(0, 128, 0, 0.25)"
                ),

                name="±1 standard error",

                hoverinfo="skip",

                line=dict(
                    width=0
                ),
            )
        )


        # Original spectrum
        fig2.add_trace(

            go.Scatter(
                x=energy_center,

                y=original_scaled_count,

                mode="lines",

                name=(
                    "Scaled original spectrum"
                ),
            )
        )


        fig2.update_layout(

            title=dict(

                text=(

                    "Original Spectrum with "
                    "Monte Carlo Uncertainty"

                    "<br><sup>"

                    f"Expected total: "
                    f"{expected_count:,.0f} ± "

                    f"{count_uncertainty:,.0f} counts "

                    f"("
                    f"{relative_uncertainty_percent:.5f}%"
                    f")"

                    "</sup>"
                ),

                x=0.5,

                xanchor="center",
            ),

            xaxis_title=(
                "Energy (keV)"
            ),

            yaxis_title=(
                "Scaled count"
            ),
        )


        st.plotly_chart(
            fig2,
            key=(
                "original_spectrum_"
                "uncertainty_chart"
            ),
            width="stretch",
        )


    # =====================================================================
    # SAVE H5 / SIMULATION OUTPUT
    # =====================================================================

    try:

        simulation_file_path = save_file(

            root_file_path.parent,

            energy=(
                energy_center
            ),

            preprocessing_count=(
                scaled_count
            ),

            original_scaled_count=(
                original_scaled_count
            ),
        )


        simulation_file_path = Path(
            simulation_file_path
        )


    except Exception as exc:

        st.error(
            f"Could not save processed spectrum: {exc}"
        )

        st.stop()


    # =====================================================================
    # CREATE DOWNLOAD ZIP
    # =====================================================================

    simulation_h5_path = (
        simulation_file_path
        / "simulation.h5"
    )


    if simulation_h5_path.exists():

        try:

            zip_path = Path(

                shutil.make_archive(

                    base_name=str(
                        simulation_file_path
                    ),

                    format="zip",

                    root_dir=(
                        simulation_file_path.parent
                    ),

                    base_dir=(
                        simulation_file_path.name
                    ),
                )
            )


            with zip_path.open(
                "rb"
            ) as zip_file:

                st.download_button(

                    label=(
                        "Download complete run folder"
                    ),

                    data=zip_file,

                    file_name=(
                        zip_path.name
                    ),

                    mime=(
                        "application/zip"
                    ),

                    icon=(
                        ":material/download:"
                    ),

                    use_container_width=True,
                )


        except Exception as exc:

            st.error(
                f"Could not create download ZIP: {exc}"
            )


    else:

        st.warning(
            "Detector processing completed, "
            "but simulation.h5 was not found."
        )