from __future__ import annotations

import json
from pathlib import Path

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
    """
    Check whether a background Geant4 process has finished.

    If it completed successfully:
        - validate simulation.root
        - register beam_on in RoboAiXrfSimulation
        - mark the frontend run as complete

    If it failed:
        - clear running state
        - report the exit code
    """

    process = st.session_state.get("geant4_process")

    if process is None:
        return

    return_code = process.poll()

    # Still running.
    if return_code is None:
        st.session_state.geant4_running = True
        return

    # Process has finished.
    st.session_state.geant4_running = False
    st.session_state.geant4_process = None

    if return_code != 0:
        st.session_state.run_complete = False
        st.session_state.last_root_file = None

        st.error(
            f"Geant4 exited with code {return_code}."
        )
        return

    sim = st.session_state.get("simulation")

    if sim is None:
        st.session_state.run_complete = False

        st.error(
            "Geant4 finished, but the simulation object "
            "is no longer available."
        )
        return

    beam_on = st.session_state.get(
        "geant4_beam_on"
    )

    if beam_on is None:
        st.session_state.run_complete = False

        st.error(
            "Geant4 finished, but the beam-on count "
            "was not stored."
        )
        return

    try:
        # This sets sim._beam_on after confirming
        # simulation.root exists.
        root_file = sim.finalize_run(
            beam_on=int(beam_on)
        )

        st.session_state.run_complete = True
        st.session_state.last_root_file = str(
            root_file
        )

        st.success(
            f"Simulation complete: {root_file}"
        )

    except Exception as exc:
        st.session_state.run_complete = False
        st.session_state.last_root_file = None

        st.exception(exc)


# ==========================================================
# LIVE GEANT4 PROCESS MONITOR
# ==========================================================

@st.fragment(run_every="1s")
def _running_simulation_panel():
    """
    Check the background Geant4 process every second.

    Only this small fragment refreshes while Geant4 is running.
    """

    process = st.session_state.get(
        "geant4_process"
    )

    if process is None:
        return

    return_code = process.poll()

    # ------------------------------------------------------
    # STILL RUNNING
    # ------------------------------------------------------

    if return_code is None:

        st.session_state.geant4_running = True

        st.info(
            f"Geant4 simulation is running — "
            f"PID {process.pid}"
        )

        if st.button(
            "■ Stop simulation",
            type="primary",
            width="stretch",
            key="stop_geant4_live",
        ):
            try:

                stopped = stop_geant4_process()

                if stopped:
                    st.warning(
                        "Simulation stopped."
                    )

                st.rerun()

            except Exception as exc:
                st.exception(exc)

        return

    # ------------------------------------------------------
    # SIMULATION FINISHED
    # ------------------------------------------------------

    _finalize_finished_process()

    # Refresh the entire page so the UI changes
    # immediately from Running -> Complete.
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

    c1, c2, c3 = st.columns(3)

    # ==========================================================
    # 1. BUILD & COMPILE
    # ==========================================================

    with c1:

        build_disabled = (
            st.session_state.get(
                "geant4_running",
                False,
            )
        )

        if st.button(
            "1. Build & compile",
            type="primary",
            disabled=build_disabled,
            width="stretch",
        ):
            try:

                with st.spinner(
                    "Building package objects and "
                    "compiling configuration..."
                ):
                    simulation = build_simulation(
                        cfg
                    )

                    simulation.compile()

                st.session_state.simulation = (
                    simulation
                )

                st.session_state.compiled_fingerprint = (
                    configuration_fingerprint(
                        cfg
                    )
                )

                st.session_state.run_complete = False
                st.session_state.noise_result = None
                st.session_state.last_root_file = None

                st.session_state.geant4_process = None
                st.session_state.geant4_running = False
                st.session_state.geant4_stopped = False
                st.session_state.geant4_beam_on = None

                st.success(
                    "Configuration compiled."
                )

            except Exception as exc:
                st.exception(exc)

    # ==========================================================
    # 2. OPEN VISUALIZATION
    # ==========================================================

    with c2:

        vis_disabled = (
            not _simulation_is_current()
            or st.session_state.get(
                "geant4_running",
                False,
            )
        )

        if st.button(
            "2. Open visualization",
            disabled=vis_disabled,
            width="stretch",
        ):
            try:

                sim = (
                    st.session_state.simulation
                )

                with st.spinner(
                    "Running visualization "
                    "histories..."
                ):

                    viewer_url = sim.show_vis(
                        beam_on=int(
                            run["vis_beam_on"]
                        ),
                        number_of_thread=int(
                            run["vis_threads"]
                        ),
                    )

                # Visualization is NOT a valid
                # quantitative simulation.
                st.session_state.run_complete = False
                st.session_state.noise_result = None
                st.session_state.last_root_file = None

                if viewer_url:

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
                        "Visualization generated."
                    )

                    st.link_button(
                        "Open 3D viewer",
                        viewer_url,
                        width="stretch",
                    )

                else:
                    st.warning(
                        "Visualization completed, "
                        "but no viewer URL was returned."
                    )

            except Exception as exc:
                st.exception(exc)

    # ==========================================================
    # 3. RUN GEANT4
    # ==========================================================

    with c3:

        run_disabled = (
            not _simulation_is_current()
            or st.session_state.get(
                "geant4_running",
                False,
            )
        )

        if st.button(
            "3. Run Geant4",
            disabled=run_disabled,
            width="stretch",
        ):
            try:

                sim = (
                    st.session_state.simulation
                )

                selected_beam_on = int(
                    run["beam_on"]
                )

                process = sim.start_run(
                    beam_on=selected_beam_on,
                    number_of_thread=int(
                        run["number_of_thread"]
                    ),
                )

                st.session_state.geant4_process = (
                    process
                )

                # Store the exact beam count associated
                # with THIS process.
                st.session_state.geant4_beam_on = (
                    selected_beam_on
                )

                st.session_state.geant4_running = (
                    True
                )

                st.session_state.geant4_stopped = (
                    False
                )

                st.session_state.run_complete = (
                    False
                )

                st.session_state.noise_result = (
                    None
                )

                st.session_state.last_root_file = (
                    None
                )

                st.rerun()

            except Exception as exc:

                st.session_state.geant4_running = (
                    False
                )

                st.exception(exc)

        # ==========================================================
        # LIVE SIMULATION STATUS
        # ==========================================================

        if st.session_state.get(
            "geant4_process"
        ) is not None:

            _running_simulation_panel()

        # ==========================================================
        # COMPLETED SIMULATION
        # ==========================================================

        elif st.session_state.get(
            "run_complete",
            False,
        ):

            root_file = st.session_state.get(
                "last_root_file"
            )

            if root_file:

                st.success(
                    f"Simulation complete: {root_file}"
                )

            else:

                st.success(
                    "Simulation complete."
                )

        # ==========================================================
        # STOPPED SIMULATION
        # ==========================================================

        elif st.session_state.get(
            "geant4_stopped",
            False,
        ):

            st.warning(
                "The previous Geant4 simulation "
                "was stopped."
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