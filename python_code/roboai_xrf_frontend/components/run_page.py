from __future__ import annotations

import json
from pathlib import Path
import time

import streamlit as st
import streamlit.components.v1 as components

from builder import build_simulation
from components.common import page_header
from state import (
    configuration_fingerprint,
    stop_geant4_process,
)


def _simulation_is_current() -> bool:
    sim = st.session_state.get("simulation")

    if sim is None:
        return False

    return (
        st.session_state.get("compiled_fingerprint")
        == configuration_fingerprint(
            st.session_state.ui_config
        )
    )


def _finalize_finished_process() -> None:

    process = st.session_state.get(
        "geant4_process"
    )

    if process is None:
        return

    return_code = process.poll()

    # Still running
    if return_code is None:
        st.session_state.geant4_running = True
        return

    # Process finished
    st.session_state.geant4_running = False
    st.session_state.geant4_process = None

    # ------------------------------------------------------
    # FAILED
    # ------------------------------------------------------

    if return_code != 0:

        st.session_state.run_complete = False
        st.session_state.last_root_file = None

        st.error(
            f"Geant4 exited with code {return_code}."
        )

        return

    # ------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------

    sim = st.session_state.get(
        "simulation"
    )

    if sim is None:

        st.session_state.run_complete = False
        st.session_state.last_root_file = None

        st.error(
            "Geant4 finished, but the simulation object "
            "is no longer available."
        )

        return

    root_file = (
        Path(sim.config_path)
        / "simulation.root"
    )

    if not root_file.is_file():

        st.session_state.run_complete = False
        st.session_state.last_root_file = None

        st.error(
            f"Geant4 finished, but simulation.root "
            f"was not found: {root_file}"
        )

        return

    # ------------------------------------------------------
    # COMPLETE
    # ------------------------------------------------------

    st.session_state.run_complete = True
    st.session_state.last_root_file = str(
        root_file
    )

from pathlib import Path


from pathlib import Path
import time




TQDM_FILE = Path(
    "/home/user/persistent/xrftest/TEMPO_XRF_REPO/"
    "python_code/roboai_xrf_frontend/tqdm_output.txt"
)


import re
from pathlib import Path

TQDM_FILE = Path(
    "/home/user/persistent/xrftest/TEMPO_XRF_REPO/"
    "python_code/roboai_xrf_frontend/tqdm_output.txt"
)

last_percent=0  
def read_last_line(path):
    if not path.exists():
        return ""

    with open(
        path,
        "r",
        encoding="utf-8",
        errors="replace",
    ) as f:

        lines = f.read().splitlines()

    if not lines:
        return ""

    return lines[-1]
@st.fragment(run_every="0.7s")
def _running_simulation_panel():

    process = st.session_state.get(
        "geant4_process"
    )

    if process is None:
        return

    # ======================================================
    # READ ONLY LAST TQDM LINE
    # ======================================================

    output = read_last_line(
        TQDM_FILE
    )

    # ======================================================
    # GET PERCENTAGE
    # ======================================================

    match = re.search(
        r"(\d+)%\|",
        output,
    )

    if match:

        percent = int(
            match.group(1)
        )

        st.session_state[
            "last_geant4_percent"
        ] = percent

    else:

        percent = st.session_state.get(
            "last_geant4_percent",
            0,
        )

    # ======================================================
    # PROGRESS BAR
    # ======================================================

    st.progress(
        percent / 100,
        text=f"Geant4: {percent}%",
    )

    # ======================================================
    # STILL RUNNING
    # ======================================================

    if process.poll() is None:

        if st.button(
            "■ Stop simulation",
            type="primary",
            width="stretch",
            key="stop_geant4_live",
        ):

            stop_geant4_process()
            st.rerun()

        return

    # ======================================================
    # FINISHED
    # ======================================================

    _finalize_finished_process()

    st.rerun()
def render_run_page():
    cfg = st.session_state.ui_config
    run = cfg["run"]

    # Check any background job whenever this page reruns.
    _finalize_finished_process()

    page_header(
        "Build & run",
        "Compile creates config.json and the SpekPy source. "
        "Run executes the Geant4 backend through the roboaixrf package.",
    )

    # ==========================================================
    # RUN SETTINGS
    # ==========================================================

    with st.form("run_settings_form"):

        c1, c2 = st.columns([1.4, 1])

        run_name = c1.text_input(
            "Run name",
            value=run["run_name"],
        )

        threads = c2.number_input(
            "Threads",
            min_value=1,
            value=int(
                run["number_of_thread"]
            ),
            step=1,
        )

        c1, c2 = st.columns(2)

        beam_on = c1.number_input(
            "Beam-on events",
            min_value=2,
            value=int(
                run["beam_on"]
            ),
            step=1000,
            format="%d",
        )

        print_display = c2.number_input(
            "Print progress every",
            min_value=1,
            value=int(
                run["print_display"]
            ),
            step=1000,
            format="%d",
        )

        c1, c2 = st.columns(2)

        vis_beam = c1.number_input(
            "Visualization events",
            min_value=1,
            value=int(
                run["vis_beam_on"]
            ),
            step=1,
        )

        vis_threads = c2.number_input(
            "Visualization threads",
            min_value=1,
            value=int(
                run["vis_threads"]
            ),
            step=1,
        )

        if st.form_submit_button(
            "Save run settings"
        ):
            run.update(
                {
                    "run_name": run_name.strip(),
                    "beam_on": int(beam_on),
                    "number_of_thread": int(
                        threads
                    ),
                    "print_display": int(
                        print_display
                    ),
                    "vis_beam_on": int(
                        vis_beam
                    ),
                    "vis_threads": int(
                        vis_threads
                    ),
                }
            )

            st.success(
                "Run settings saved."
            )

    st.divider()

    # ==========================================================
    # ACTION BUTTONS
    # ==========================================================

    build_disabled = st.session_state.get(
        "geant4_running",
        False,
    )

    vis_disabled = (
        not _simulation_is_current()
        or st.session_state.get(
            "geant4_running",
            False,
        )
    )

    run_disabled = (
        not _simulation_is_current()
        or st.session_state.get(
            "geant4_running",
            False,
        )
    )

    # ----------------------------------------------------------
    # BUTTON ROW
    # ----------------------------------------------------------

    c1, c2, c3 = st.columns(3)

    build_clicked = c1.button(
        "1. Build & compile",
        type="primary",
        disabled=build_disabled,
        width="stretch",
    )

    vis_clicked = c2.button(
        "2. Open visualization",
        disabled=vis_disabled,
        width="stretch",
    )

    run_clicked = c3.button(
        "3. Run Geant4",
        disabled=run_disabled,
        width="stretch",
    )
    if st.session_state.pop(
        "build_success",
        False,
    ):
        st.success(
            "Configuration compiled.",
            width="stretch",
        )

    # ==========================================================
    # FULL-WIDTH ACTION / STATUS AREA
    # ==========================================================

    # ----------------------------------------------------------
    # 1. BUILD & COMPILE
    # ----------------------------------------------------------

    if build_clicked:

        try:

            with st.spinner(
                "Building package objects and compiling configuration..."
            ):

                simulation = build_simulation(cfg)

                simulation.compile()

            st.session_state.simulation = simulation

            st.session_state.compiled_fingerprint = (
                configuration_fingerprint(cfg)
            )

            st.session_state.run_complete = False
            st.session_state.noise_result = None
            st.session_state.last_root_file = None

            st.session_state.geant4_process = None
            st.session_state.geant4_running = False
            st.session_state.geant4_stopped = False
            st.session_state.geant4_beam_on = None

            # Clear old visualization
            st.session_state.viewer_url = None

            # st.success(
            #     "Configuration compiled.",
            #     width="stretch",
            # )
            st.session_state.build_success = True

            st.rerun()
        except Exception as exc:
            st.exception(exc)

    # ----------------------------------------------------------
    # 2. OPEN VISUALIZATION
    # ----------------------------------------------------------

    if vis_clicked:

        try:

            sim = st.session_state.simulation

            with st.spinner(
                "Running visualization histories..."
            ):

                viewer_url = sim.show_vis(
                    beam_on=int(
                        run["vis_beam_on"]
                    ),
                    number_of_thread=int(
                        run["vis_threads"]
                    ),
                )

            # Visualization is NOT a valid quantitative run.
            st.session_state.run_complete = False
            st.session_state.noise_result = None
            st.session_state.last_root_file = None

            if viewer_url:

                st.session_state.viewer_url = viewer_url

                components.html(
                    f"""
                    <script>
                        window.parent.open(
                            "{viewer_url}",
                            "_blank"
                        );
                    </script>
                    """,
                    height=0,
                )

                st.success(
                    "Visualization generated.",
                    width="stretch",
                )

            else:

                st.session_state.viewer_url = None

                st.warning(
                    "Visualization completed, "
                    "but no viewer URL was returned.",
                    width="stretch",
                )

        except Exception as exc:
            st.exception(exc)

    # ----------------------------------------------------------
    # PERSISTENT VISUALIZATION LINK
    # ----------------------------------------------------------

    viewer_url = st.session_state.get(
        "viewer_url"
    )

    if (
        viewer_url
        and not st.session_state.get(
            "geant4_running",
            False,
        )
    ):

        st.link_button(
            "Open 3D viewer",
            viewer_url,
            width="stretch",
        )

    # ----------------------------------------------------------
    # 3. RUN GEANT4
    # ----------------------------------------------------------

    if run_clicked:

        try:

            sim = st.session_state.simulation

            selected_beam_on = int(
                run["beam_on"]
            )

            process = sim.start_run(
                beam_on=selected_beam_on,
                number_of_thread=int(
                    run["number_of_thread"]
                ),
            )
            st.session_state.geant4_started_at = time.time()

            st.session_state.geant4_process = (
                process
            )

            # Store the exact beam count belonging
            # to this process.
            st.session_state.geant4_beam_on = (
                selected_beam_on
            )

            st.session_state.geant4_running = True
            st.session_state.geant4_stopped = False

            st.session_state.run_complete = False
            st.session_state.noise_result = None
            st.session_state.last_root_file = None

            st.rerun()

        except Exception as exc:

            st.session_state.geant4_running = False

            st.exception(exc)

    # ==========================================================
    # LIVE / FINISHED SIMULATION STATUS
    # FULL WIDTH because this is NOT inside c3
    # ==========================================================

    if st.session_state.get(
        "geant4_process"
    ) is not None:

        _running_simulation_panel()

    elif st.session_state.get(
        "run_complete",
        False,
    ):

        root_file = st.session_state.get(
            "last_root_file"
        )

        if root_file:

            st.success(
                f"Simulation complete: {root_file}",
                width="stretch",
            )

        else:

            st.success(
                "Simulation complete.",
                width="stretch",
            )

    elif st.session_state.get(
        "geant4_stopped",
        False,
    ):

        st.warning(
            "The previous Geant4 simulation was stopped.",
            width="stretch",
        )

    st.divider()

    # ==========================================================
    # GENERATED CONFIGURATION
    # ==========================================================

    st.subheader(
        "Generated configuration"
    )

    if _simulation_is_current():

        config_path = (
            Path(
                st.session_state
                .simulation
                .config_path
            )
            / "config.json"
        )

        if config_path.is_file():

            text = config_path.read_text(
                encoding="utf-8"
            )

            left, right = st.columns(
                [3, 1]
            )

            with left:

                with st.expander(
                    "Preview config.json",
                    expanded=False,
                ):
                    st.json(
                        json.loads(text)
                    )

            with right:

                st.download_button(
                    "Download config.json",
                    data=text,
                    file_name="config.json",
                    mime="application/json",
                    width="stretch",
                )

        else:

            st.caption(
                "Compile the configuration "
                "to generate config.json."
            )

    else:

        st.caption(
            "No current compiled configuration."
        )