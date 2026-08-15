import json
import os
import signal
import subprocess

from collections import deque
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import numpy as np
import plotly.express as px
import streamlit as st

from helper.xray_tube import get_flu


BUILDIR = Path("../../build/").resolve()


# =========================================================================
# HELPERS
# =========================================================================


def get_nested(data: dict, *keys):
    value = data

    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise KeyError(" -> ".join(keys))

        value = value[key]

    return value


def validate_simulation_config(config: dict) -> list[str]:

    required_paths = [
        ("xray_tube", "current_ma"),
        ("xray_tube", "voltage_kv"),
        ("xray_tube", "anode_angle_deg"),
        ("xray_tube", "anode_symbol"),
        ("xray_tube", "sample_to_focal_spot_mm"),

        ("geometry", "tube", "filters"),

        (
            "geometry",
            "sample",
            "sample_to_tube_collimator_distance_mm",
        ),

        (
            "geometry",
            "sample",
            "tube_collimator_radius_mm",
        ),

        ("geometry",),
        ("physics",),
    ]

    missing = []

    for path in required_paths:

        try:
            get_nested(
                config,
                *path,
            )

        except KeyError:
            missing.append(
                " -> ".join(path)
            )

    return missing


def load_uploaded_json(uploaded_file):

    if uploaded_file is None:
        return None

    try:

        uploaded_file.seek(0)

        return json.load(
            uploaded_file
        )

    except json.JSONDecodeError as exc:

        st.error(
            f"Invalid JSON file: {exc}"
        )

        return None

    except Exception as exc:

        st.error(
            f"Could not read JSON file: {exc}"
        )

        return None


def tail_file(
    path: Path,
    number_of_lines: int = 30,
) -> str:

    if not path.exists():
        return ""

    try:

        with path.open(
            "r",
            encoding="utf-8",
            errors="replace",
        ) as f:

            lines = deque(
                f,
                maxlen=number_of_lines,
            )

        return "".join(lines)

    except Exception:
        return ""


def calculate_beam_geometry(
    sample_to_focal_spot_source: float,
    sample_to_tube_collimator: float,
    tube_collimator_radius: float,
):

    d1 = (
        sample_to_focal_spot_source
        - sample_to_tube_collimator
    )

    d2 = sample_to_tube_collimator

    if d1 <= 0:

        raise ValueError(
            "The tube collimator must be between "
            "the focal spot and the sample."
        )

    beam_radius_mm = (
        tube_collimator_radius
        * (d1 + d2)
        / d1
    )

    beam_area_cm2 = (
        np.pi
        * (beam_radius_mm / 10.0) ** 2
    )

    return (
        float(beam_radius_mm),
        float(beam_area_cm2),
    )


def get_simulation_process():

    run_info = st.session_state.get(
        "simulation_run"
    )

    if not run_info:
        return None

    return run_info.get(
        "process"
    )


def simulation_is_running() -> bool:

    process = get_simulation_process()

    if process is None:
        return False

    try:
        return process.poll() is None

    except Exception:
        return False


# =========================================================================
# FINALIZE COMPLETED SIMULATION
# =========================================================================


def finalize_simulation(
    run_info: dict,
):

    if run_info.get(
        "finalized",
        False,
    ):
        return

    folder_path = Path(
        run_info["folder_path"]
    )

    root_file_path = Path(
        run_info["root_file_path"]
    )

    updated_json_path = (
        folder_path
        / "updated_config.json"
    ).resolve()

    # ---------------------------------------------------------
    # Make sure ROOT output really exists.
    # ---------------------------------------------------------

    if not root_file_path.exists():

        raise FileNotFoundError(
            "Geant4 returned successfully but "
            f"the ROOT file does not exist:\n{root_file_path}"
        )

    # ---------------------------------------------------------
    # Load geometry-updated config produced by Geant4.
    #
    # The user DOES NOT upload this.
    # ---------------------------------------------------------

    if updated_json_path.exists():

        with updated_json_path.open(
            "r",
            encoding="utf-8",
        ) as f:

            updated_config = json.load(
                f
            )

    else:

        # Fallback.
        updated_config = deepcopy(
            run_info["config"]
        )

    # ---------------------------------------------------------
    # Add simulation information.
    # ---------------------------------------------------------

    updated_config["simulation"] = {

        "file_name":
            run_info["file_name"],

        "root_file_name":
            root_file_path.name,

        "beam_on_events":
            int(
                run_info["beamon"]
            ),

        "number_of_threads":
            int(
                run_info["numberof_thread"]
            ),

        "one_second_photon":
            float(
                run_info["flu_number"]
            ),

        "beam_radius_mm":
            float(
                run_info["beam_radius_mm"]
            ),

        "beam_area_cm2":
            float(
                run_info["beam_area_cm2"]
            ),
    }

    # ---------------------------------------------------------
    # Save updated_config.json automatically.
    # ---------------------------------------------------------

    with updated_json_path.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            updated_config,
            f,
            indent=4,
            ensure_ascii=False,
        )

    # ---------------------------------------------------------
    # Save everything your detector-noise / plotting page needs.
    #
    # NO JSON UPLOAD REQUIRED.
    # ---------------------------------------------------------

    st.session_state[
        "simulation_status"
    ] = True

    st.session_state[
        "root_file_path"
    ] = str(
        root_file_path
    )

    st.session_state[
        "one_second_photon"
    ] = float(
        run_info["flu_number"]
    )

    st.session_state[
        "area_on_sample"
    ] = float(
        run_info["beam_area_cm2"]
    )

    st.session_state[
        "beamon"
    ] = int(
        run_info["beamon"]
    )

    st.session_state[
        "voltage"
    ] = float(
        run_info["voltage"]
    )

    st.session_state[
        "simulation_updated_config_path"
    ] = str(
        updated_json_path
    )

    # ---------------------------------------------------------
    # Store final run state.
    # ---------------------------------------------------------

    run_info[
        "finalized"
    ] = True

    run_info[
        "updated_json_path"
    ] = str(
        updated_json_path
    )

    run_info[
        "end_time"
    ] = datetime.now().isoformat()

    run_info[
        "finalization_error"
    ] = None

    st.session_state[
        "simulation_run"
    ] = run_info


# =========================================================================
# STOP SIMULATION
# =========================================================================


def stop_simulation(
    run_info: dict,
):

    process = run_info.get(
        "process"
    )

    if process is None:
        return

    if process.poll() is not None:
        return

    try:

        # ./sim was started using:
        #
        # start_new_session=True
        #
        # so it owns its own process group.
        process_group_id = os.getpgid(
            process.pid
        )

        # First ask it to terminate.
        os.killpg(
            process_group_id,
            signal.SIGTERM,
        )

        try:

            process.wait(
                timeout=5
            )

        except subprocess.TimeoutExpired:

            # Force kill if necessary.
            os.killpg(
                process_group_id,
                signal.SIGKILL,
            )

            process.wait()

    except ProcessLookupError:
        pass

    except Exception as exc:

        st.error(
            f"Could not stop simulation: {exc}"
        )

        return

    run_info[
        "stopped"
    ] = True

    run_info[
        "return_code"
    ] = process.poll()

    run_info[
        "end_time"
    ] = datetime.now().isoformat()

    st.session_state[
        "simulation_run"
    ] = run_info

    st.session_state[
        "simulation_status"
    ] = False


# =========================================================================
# LIVE SIMULATION MONITOR
# =========================================================================


@st.fragment(
    run_every="1s"
)
def show_simulation_status():

    run_info = st.session_state.get(
        "simulation_run"
    )

    if not run_info:
        return

    process = run_info.get(
        "process"
    )

    if process is None:

        st.warning(
            "The simulation process handle is unavailable."
        )

        return

    log_path = Path(
        run_info["log_file_path"]
    )

    try:

        return_code = process.poll()

    except Exception as exc:

        st.error(
            f"Could not check Geant4 process: {exc}"
        )

        return

    # =====================================================================
    # PROCESS JUST FINISHED
    #
    # This detects the state transition once.
    # =====================================================================

    if (
        return_code is not None
        and run_info.get("return_code") is None
    ):

        run_info[
            "return_code"
        ] = return_code

        if not run_info.get(
            "end_time"
        ):

            run_info[
                "end_time"
            ] = datetime.now().isoformat()

        st.session_state[
            "simulation_run"
        ] = run_info

        # -----------------------------------------------------
        # Successful Geant4 completion
        # -----------------------------------------------------

        if (
            return_code == 0
            and not run_info.get(
                "stopped",
                False,
            )
        ):

            try:

                finalize_simulation(
                    run_info
                )

            except Exception as exc:

                run_info[
                    "finalization_error"
                ] = str(exc)

                run_info[
                    "finalized"
                ] = False

                st.session_state[
                    "simulation_run"
                ] = run_info

                st.session_state[
                    "simulation_status"
                ] = False

        else:

            st.session_state[
                "simulation_status"
            ] = False

        # Full rerun so that the rest of the page knows
        # the process is no longer running.
        st.rerun()

    # =====================================================================
    # RUNNING
    # =====================================================================

    if return_code is None:

        st.subheader(
            f"Running: {run_info['file_name']}"
        )

        status_col, stop_col = st.columns(
            [4, 1]
        )

        with status_col:

            st.success(
                f"Geant4 is running — PID {run_info['pid']}"
            )

        with stop_col:

            if st.button(
                "Stop simulation",
                type="primary",
                use_container_width=True,
                key=(
                    f"stop_simulation_"
                    f"{run_info['pid']}"
                ),
            ):

                stop_simulation(
                    run_info
                )

                st.rerun()

        # -----------------------------------------------------
        # Time
        # -----------------------------------------------------

        try:

            start_time = datetime.fromisoformat(
                run_info["start_time"]
            )

            elapsed = (
                datetime.now()
                - start_time
            )

            st.write(
                "Elapsed:",
                str(elapsed).split(".")[0],
            )

        except Exception:
            pass

        # -----------------------------------------------------
        # Log
        # -----------------------------------------------------

        latest_output = tail_file(
            log_path,
            number_of_lines=30,
        )

        if latest_output:

            st.code(
                latest_output,
                language=None,
            )

        else:

            st.code(
                "Waiting for Geant4 output...",
                language=None,
            )

        return

    # =====================================================================
    # STOPPED BY USER
    # =====================================================================

    if run_info.get(
        "stopped",
        False,
    ):

        st.warning(
            f"Simulation '{run_info['file_name']}' was stopped."
        )

        try:

            start_time = datetime.fromisoformat(
                run_info["start_time"]
            )

            end_time = datetime.fromisoformat(
                run_info["end_time"]
            )

            st.write(
                "Run time:",
                str(
                    end_time - start_time
                ).split(".")[0],
            )

        except Exception:
            pass

        latest_output = tail_file(
            log_path,
            number_of_lines=30,
        )

        if latest_output:

            with st.expander(
                "Geant4 log",
                expanded=False,
            ):

                st.code(
                    latest_output,
                    language=None,
                )

        return

    # =====================================================================
    # SUCCESS
    # =====================================================================

    if return_code == 0:

        finalization_error = run_info.get(
            "finalization_error"
        )

        if finalization_error:

            st.error(
                "Geant4 completed, but saving run information failed:\n\n"
                f"{finalization_error}"
            )

            latest_output = tail_file(
                log_path,
                number_of_lines=30,
            )

            if latest_output:

                with st.expander(
                    "Geant4 log"
                ):

                    st.code(
                        latest_output,
                        language=None,
                    )

            return

        st.success(
            f"Simulation '{run_info['file_name']}' completed."
        )

        # -----------------------------------------------------
        # Time
        # -----------------------------------------------------

        try:

            start_time = datetime.fromisoformat(
                run_info["start_time"]
            )

            end_time = datetime.fromisoformat(
                run_info["end_time"]
            )

            elapsed = (
                end_time
                - start_time
            )

            st.write(
                "Time taken:",
                str(elapsed).split(".")[0],
            )

        except Exception:
            pass

        # -----------------------------------------------------
        # Output paths
        # -----------------------------------------------------

        root_path = Path(
            run_info["root_file_path"]
        )

        st.write(
            "ROOT file:",
            root_path.name,
        )

        updated_json_path = run_info.get(
            "updated_json_path"
        )

        if updated_json_path:

            st.write(
                "Run configuration:",
                Path(
                    updated_json_path
                ).name,
            )

        # -----------------------------------------------------
        # Log is collapsed after completion.
        # -----------------------------------------------------

        latest_output = tail_file(
            log_path,
            number_of_lines=30,
        )

        if latest_output:

            with st.expander(
                "Geant4 log",
                expanded=False,
            ):

                st.code(
                    latest_output,
                    language=None,
                )

        return

    # =====================================================================
    # FAILED
    # =====================================================================

    st.error(
        f"Geant4 stopped with exit code {return_code}."
    )

    latest_output = tail_file(
        log_path,
        number_of_lines=30,
    )

    if latest_output:

        with st.expander(
            "Geant4 log",
            expanded=True,
        ):

            st.code(
                latest_output,
                language=None,
            )


# =========================================================================
# SHOW CURRENT RUN FIRST
# =========================================================================


# =========================================================================
# SHOW CURRENT RUN FIRST
# =========================================================================

show_simulation_status()


# =========================================================================
# EXISTING RUN
#
# While Geant4 is running:
#     only show the run monitor.
#
# When Geant4 stops/completes:
#     continue below and show the SAME simulation form again.
#
# No "New simulation" state reset is necessary.
# =========================================================================

active_run = st.session_state.get(
    "simulation_run"
)


if active_run:

    # ---------------------------------------------------------------------
    # Restore EXACT SAME simulation widget keys if Streamlit removed them.
    # ---------------------------------------------------------------------

    if (
        "simulation_file_name"
        not in st.session_state
    ):

        st.session_state[
            "simulation_file_name"
        ] = active_run[
            "file_name"
        ]


    if (
        "simulation_number_of_thread"
        not in st.session_state
    ):

        st.session_state[
            "simulation_number_of_thread"
        ] = active_run[
            "numberof_thread"
        ]


    if (
        "simulation_beamon"
        not in st.session_state
    ):

        st.session_state[
            "simulation_beamon"
        ] = active_run[
            "beamon"
        ]


    # ---------------------------------------------------------------------
    # Keep configuration that was actually used by the simulation.
    #
    # Do NOT overwrite a newer config if one already exists.
    # ---------------------------------------------------------------------

    if (
        "complete_simulation_config"
        not in st.session_state
    ):

        st.session_state[
            "complete_simulation_config"
        ] = deepcopy(
            active_run["config"]
        )


    # ---------------------------------------------------------------------
    # If we already have a config from the run, don't make the user upload
    # it again.
    # ---------------------------------------------------------------------

    if (
        "simulation_config_source"
        not in st.session_state
    ):

        st.session_state[
            "simulation_config_source"
        ] = "Use current configuration"


    # ---------------------------------------------------------------------
    # Is Geant4 still running?
    # ---------------------------------------------------------------------

    active_process = active_run.get(
        "process"
    )

    active_running = False

    if active_process is not None:

        try:

            active_running = (
                active_process.poll()
                is None
            )

        except Exception:

            active_running = False


    # ---------------------------------------------------------------------
    # While running, only show monitor + STOP button.
    #
    # The configuration values are safely preserved.
    # ---------------------------------------------------------------------

    if active_running:
        st.stop()


# =========================================================================
# If execution reaches here:
#
# - there is no run
# OR
# - previous run completed
# OR
# - previous run was stopped
# OR
# - previous run failed
#
# Therefore show the simulation controls again.
# =========================================================================# =========================================================================
# NEW SIMULATION CONFIGURATION
# =========================================================================


st.subheader(
    "Start simulation"
)


session_config = st.session_state.get(
    "complete_simulation_config"
)


# =========================================================================
# CONFIGURATION SOURCE
# =========================================================================


if session_config:

    config_source = st.radio(
        "Configuration source",
        [
            "Use current configuration",
            "Upload JSON configuration",
        ],
        horizontal=True,
        key="simulation_config_source",
    )

else:

    st.info(
        "The X-ray tube / geometry parameters are not complete. "
        "You can upload a complete simulation configuration."
    )

    config_source = (
        "Upload JSON configuration"
    )


config = None
uploaded_file = None


# =========================================================================
# USE CURRENT APPLICATION CONFIGURATION
# =========================================================================


if (
    config_source
    == "Use current configuration"
):

    config = deepcopy(
        session_config
    )

    st.success(
        "Using the current application configuration."
    )


# =========================================================================
# UPLOAD INITIAL SIMULATION CONFIGURATION
#
# This is NOT updated_config.json.
#
# This is only for starting a simulation when the geometry/configuration
# was not created inside the current Streamlit session.
# =========================================================================


else:

    uploaded_file = st.file_uploader(
        "Upload simulation configuration",
        type=["json"],
        help=(
            "Upload the simulation input configuration containing "
            "xray_tube, geometry, and physics."
        ),
    )

    config = load_uploaded_json(
        uploaded_file
    )

    if config is not None:

        st.success(
            f"Loaded: {uploaded_file.name}"
        )


# =========================================================================
# NO CONFIGURATION
# =========================================================================


if config is None:
    st.stop()


# =========================================================================
# VALIDATE CONFIGURATION
# =========================================================================


missing_fields = validate_simulation_config(
    config
)


if missing_fields:

    st.error(
        "The selected configuration is missing parameters "
        "required by the simulation."
    )

    with st.expander(
        "Missing JSON fields",
        expanded=True,
    ):

        for field in missing_fields:

            st.write(
                f"• {field}"
            )

    st.stop()


with st.expander(
    "Selected configuration preview"
):

    st.json(
        config
    )


# =========================================================================
# READ X-RAY / GEOMETRY VALUES
# =========================================================================


xray_tube = config[
    "xray_tube"
]

geometry = config[
    "geometry"
]

sample = geometry[
    "sample"
]


current = float(
    xray_tube[
        "current_ma"
    ]
)

voltage = float(
    xray_tube[
        "voltage_kv"
    ]
)

anode_angle_degree = float(
    xray_tube[
        "anode_angle_deg"
    ]
)

anode_symbol = str(
    xray_tube[
        "anode_symbol"
    ]
)

sample_to_focal_spot_source = float(
    xray_tube[
        "sample_to_focal_spot_mm"
    ]
)

sample_to_tube_collimator = float(
    sample[
        "sample_to_tube_collimator_distance_mm"
    ]
)

tube_collimator_radius = float(
    sample[
        "tube_collimator_radius_mm"
    ]
)


# =========================================================================
# X-RAY TUBE FILTERS
# =========================================================================


xray_tube_filter_config = (
    geometry[
        "tube"
    ][
        "filters"
    ]
)


filters = xray_tube_filter_config.get(
    "filters",
    [],
)


filter_engine = xray_tube_filter_config.get(
    "filter_engine"
)


# =========================================================================
# RUN PARAMETERS
# =========================================================================


st.divider()


file_name = st.text_input(
    "File name",
    key="simulation_file_name",
).strip()


numberof_thread = int(
    st.number_input(
        "Number of threads",
        min_value=1,
        value=1,
        step=1,
        key="simulation_number_of_thread",
    )
)


beamon = int(
    st.number_input(
        "Beam-on events",
        min_value=1,
        value=100000,
        step=1000,
        key="simulation_beamon",
    )
)


if not file_name:

    st.warning(
        "Enter a file name to enable Geant4 controls."
    )

    st.stop()


# =========================================================================
# RUN FOLDER
# =========================================================================


folder_path = (
    Path("runs")
    / f"roboai_xrf_{file_name}"
)


folder_path.mkdir(
    parents=True,
    exist_ok=True,
)


json_file_path = (
    folder_path
    / "config.json"
).resolve()


# =========================================================================
# WRITE INPUT CONFIG
# =========================================================================


with json_file_path.open(
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        config,
        f,
        indent=4,
        ensure_ascii=False,
    )


# =========================================================================
# SHOW GEOMETRY
# =========================================================================


if st.button(
    "Show geometry in Geant4",
    key="show_geometry_in_geant4",
):

    try:

        subprocess.run(
            [
                "./sim",
                str(json_file_path),
            ],
            cwd=BUILDIR,
            check=True,
            text=True,
        )

    except subprocess.CalledProcessError as exc:

        st.error(
            "Geant4 geometry preview stopped "
            f"with code {exc.returncode}."
        )

    except Exception as exc:

        st.error(
            f"Could not start Geant4 geometry preview: {exc}"
        )


# =========================================================================
# GENERATE SPEKPY SPECTRUM
# =========================================================================


try:

    (
        energy_bin,
        flu_list,
        flu_number,
    ) = get_flu(

        current=current,

        voltage=voltage,

        exposure_time=1,

        anode_degree=(
            anode_angle_degree
        ),

        anode_target_material=(
            anode_symbol
        ),

        filters=filters,

        filter_engine=(
            filter_engine
        ),

        source_to_sample=(
            sample_to_focal_spot_source
        ),
    )

except Exception as exc:

    st.error(
        f"Could not generate X-ray spectrum: {exc}"
    )

    st.stop()


# =========================================================================
# SHOW SPECTRUM
# =========================================================================


if st.button(
    "Show spectrum distribution",
    key="show_spectrum_distribution",
):

    with st.expander(
        "X-ray spectrum",
        expanded=True,
    ):

        figure = px.line(
            x=energy_bin,
            y=flu_list,
            labels={
                "x": "Energy",
                "y": "Fluence",
            },
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )


# =========================================================================
# START SIMULATION BUTTON
# =========================================================================


start_clicked = st.button(
    "Start shooting",
    type="primary",
    key="start_geant4_simulation",
)


if start_clicked:

    # =====================================================================
    # CALCULATE BEAM AREA BEFORE STARTING
    # =====================================================================

    try:

        (
            beam_radius_mm,
            beam_area_cm2,
        ) = calculate_beam_geometry(

            sample_to_focal_spot_source=(
                sample_to_focal_spot_source
            ),

            sample_to_tube_collimator=(
                sample_to_tube_collimator
            ),

            tube_collimator_radius=(
                tube_collimator_radius
            ),
        )

    except ValueError as exc:

        st.error(
            str(exc)
        )

        st.stop()


    # =====================================================================
    # OUTPUT PATHS
    # =====================================================================

    ROOTFILEPATH = (
        folder_path
        / f"{file_name}.root"
    ).resolve()


    LOGFILEPATH = (
        folder_path
        / "simulation.log"
    ).resolve()


    MACROFILEPATH = (
        folder_path
        / "run.mac"
    ).resolve()


    UPDATEDJSONPATH = (
        folder_path
        / "updated_config.json"
    ).resolve()


    # =====================================================================
    # REMOVE OLD updated_config.json IF SAME RUN NAME IS REUSED
    # =====================================================================

    try:

        if UPDATEDJSONPATH.exists():

            UPDATEDJSONPATH.unlink()

    except Exception as exc:

        st.error(
            "Could not remove old updated_config.json: "
            f"{exc}"
        )

        st.stop()


    # =====================================================================
    # BUILD GEANT4 MACRO
    # =====================================================================

    macro_lines = [

        f"/xrf/fileName {ROOTFILEPATH}",

        (
            "/run/numberOfThreads "
            f"{numberof_thread}"
        ),

        "/run/initialize",

        "/gps/particle gamma",

        "/gps/ene/type User",

        "/gps/hist/type energy",
    ]


    for energy, fluence in zip(
        energy_bin,
        flu_list,
    ):

        macro_lines.append(
            "/gps/hist/point "
            f"{energy / 1000} "
            f"{fluence}"
        )


    macro_lines.extend(
        [
            "/run/printProgress 100000",
            f"/run/beamOn {beamon}",
        ]
    )


    macro_file = (
        "\n".join(
            macro_lines
        )
        + "\n"
    )


    # =====================================================================
    # WRITE MACRO
    # =====================================================================

    with MACROFILEPATH.open(
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            macro_file
        )


    # =====================================================================
    # START GEANT4
    #
    # Geant4 writes directly to simulation.log.
    #
    # Therefore switching Streamlit pages does NOT break stdout handling.
    # =====================================================================

    try:

        log_file = LOGFILEPATH.open(
            "w",
            encoding="utf-8",
        )

        try:

            process = subprocess.Popen(
                [
                    "./sim",
                    str(json_file_path),
                    str(MACROFILEPATH),
                ],

                cwd=BUILDIR,

                stdout=log_file,

                stderr=subprocess.STDOUT,

                # Allows Stop Simulation to kill the complete
                # Geant4 process group safely.
                start_new_session=True,
            )

        finally:

            # Child owns its duplicated descriptor now.
            log_file.close()

    except Exception as exc:

        st.error(
            f"Could not start Geant4 simulation: {exc}"
        )

        st.stop()


    # =====================================================================
    # A NEW SIMULATION IS NOW RUNNING
    #
    # Prevent Plot / detector-noise page from using incomplete ROOT output.
    # =====================================================================

    st.session_state[
        "simulation_status"
    ] = False


    # =====================================================================
    # SAVE KNOWN VALUES IMMEDIATELY
    #
    # No need to ask the user for these values again later.
    # =====================================================================

    st.session_state[
        "root_file_path"
    ] = str(
        ROOTFILEPATH
    )


    st.session_state[
        "one_second_photon"
    ] = float(
        flu_number
    )


    st.session_state[
        "area_on_sample"
    ] = float(
        beam_area_cm2
    )


    st.session_state[
        "beamon"
    ] = int(
        beamon
    )


    st.session_state[
        "voltage"
    ] = float(
        voltage
    )


    st.session_state[
        "simulation_updated_config_path"
    ] = str(
        UPDATEDJSONPATH
    )


    # =====================================================================
    # SAVE RUN CONTROLLER
    # =====================================================================

    st.session_state[
        "simulation_run"
    ] = {

        # -----------------------------------------------------
        # Process
        # -----------------------------------------------------

        "process":
            process,

        "pid":
            process.pid,

        # -----------------------------------------------------
        # Run identity
        # -----------------------------------------------------

        "file_name":
            file_name,

        # -----------------------------------------------------
        # Paths
        # -----------------------------------------------------

        "folder_path":
            str(
                folder_path.resolve()
            ),

        "root_file_path":
            str(
                ROOTFILEPATH
            ),

        "log_file_path":
            str(
                LOGFILEPATH
            ),

        "macro_file_path":
            str(
                MACROFILEPATH
            ),

        "config_file_path":
            str(
                json_file_path
            ),

        "updated_json_path":
            str(
                UPDATEDJSONPATH
            ),

        # -----------------------------------------------------
        # Configuration snapshot
        # -----------------------------------------------------

        "config":
            deepcopy(
                config
            ),

        # -----------------------------------------------------
        # Timing
        # -----------------------------------------------------

        "start_time":
            datetime.now().isoformat(),

        "end_time":
            None,

        # -----------------------------------------------------
        # Run settings
        # -----------------------------------------------------

        "beamon":
            int(
                beamon
            ),

        "numberof_thread":
            int(
                numberof_thread
            ),

        # -----------------------------------------------------
        # X-ray information
        # -----------------------------------------------------

        "flu_number":
            float(
                flu_number
            ),

        "voltage":
            float(
                voltage
            ),

        # -----------------------------------------------------
        # Geometry values
        # -----------------------------------------------------

        "sample_to_focal_spot_source":
            float(
                sample_to_focal_spot_source
            ),

        "sample_to_tube_collimator":
            float(
                sample_to_tube_collimator
            ),

        "tube_collimator_radius":
            float(
                tube_collimator_radius
            ),

        # -----------------------------------------------------
        # Already calculated beam geometry
        # -----------------------------------------------------

        "beam_radius_mm":
            float(
                beam_radius_mm
            ),

        "beam_area_cm2":
            float(
                beam_area_cm2
            ),

        # -----------------------------------------------------
        # State
        # -----------------------------------------------------

        "finalized":
            False,

        "stopped":
            False,

        "return_code":
            None,

        "finalization_error":
            None,
    }


    # =====================================================================
    # RERUN
    #
    # The configuration UI disappears.
    # The live simulation monitor becomes the page.
    # =====================================================================
    st.rerun()