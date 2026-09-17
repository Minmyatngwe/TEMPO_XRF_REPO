import base64
from pathlib import Path

import streamlit as st

from theme import apply_roboai_libs_theme
from state import (
    init_state,
    reset_all,
    configuration_fingerprint,
)

from components.setup_page import render_setup_page
from components.tube_page import render_tube_page
from components.detector_page import render_detector_page
from components.physics_page import render_physics_page
from components.run_page import render_run_page
from components.results_page import render_results_page
from components.docs_page import render_docs_page


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="RoboAI XRF",
    page_icon="⚛",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# LOGO HELPERS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "roboai_logo.png"


def _logo_base64() -> str:
    return base64.b64encode(
        LOGO_PATH.read_bytes()
    ).decode("utf-8")


def render_main_logo():
    logo = _logo_base64()

    st.markdown(
        f"""
        <div class="roboai-main-logo">
            <img
                src="data:image/png;base64,{logo}"
                alt="RoboAI"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_logo():
    logo = _logo_base64()

    st.markdown(
        f"""
        <div class="roboai-sidebar-logo">
            <img
                src="data:image/png;base64,{logo}"
                alt="RoboAI"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# THEME + SESSION
# ==========================================================

apply_roboai_libs_theme()
init_state()


# ==========================================================
# DOCUMENTATION STATE
# ==========================================================

if "show_docs" not in st.session_state:
    st.session_state.show_docs = False


def _leave_docs():
    st.session_state.show_docs = False


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    render_sidebar_logo()

    st.markdown(
        '<div class="sidebar-product-name">XRF Simulation</div>',
        unsafe_allow_html=True,
    )

    st.caption("Geant4 XRF simulation interface")

    # ======================================================
    # DOCUMENTATION
    # ======================================================

    if st.button(
        "Documentation",
        use_container_width=True,
        key="open_documentation",
    ):
        st.session_state.show_docs = True
        st.rerun()

    st.divider()

    # ======================================================
    # NAVIGATION
    # ======================================================

    page = st.radio(
        "Navigation",
        [
            "Setup",
            "X-ray tube",
            "Detector",
            "Physics",
            "Build & run",
            "Results",
        ],
        label_visibility="collapsed",
        key="navigation_page",
        on_change=_leave_docs,
    )

    st.divider()

    # ======================================================
    # ACTIVE CONFIGURATION
    # ======================================================

    loaded_name = st.session_state.get(
        "loaded_config_name"
    )

    config_was_imported = st.session_state.get(
        "config_was_imported",
        False,
    )

    st.caption("Active configuration")

    if config_was_imported and loaded_name:

        st.markdown(
            f"**📄 {loaded_name}**"
        )

        st.caption(
            "Imported RoboAI configuration"
        )

    else:

        st.markdown(
            "**Example defaults**"
        )

        st.caption(
            "Using frontend default configuration"
        )

    st.divider()

    # ======================================================
    # SIMULATION STATUS
    # ======================================================

    sim = st.session_state.get(
        "simulation"
    )

    geant4_running = st.session_state.get(
        "geant4_running",
        False,
    )

    geant4_stopped = st.session_state.get(
        "geant4_stopped",
        False,
    )

    run_complete = st.session_state.get(
        "run_complete",
        False,
    )

    compiled_fingerprint = st.session_state.get(
        "compiled_fingerprint"
    )

    is_current = (
        sim is not None
        and compiled_fingerprint
        == configuration_fingerprint(
            st.session_state.ui_config
        )
    )

    st.caption("Simulation status")

    if geant4_running:

        process = st.session_state.get(
            "geant4_process"
        )

        if process is not None:
            st.markdown(
                f"🟣 **Running** · PID {process.pid}"
            )
        else:
            st.markdown(
                "🟣 **Running**"
            )

    elif sim is None:

        st.markdown(
            "⚪ **Not compiled**"
        )

    elif not is_current:

        st.markdown(
            "🟡 **Configuration changed**"
        )

        st.caption(
            "Build & compile again before running."
        )

    elif geant4_stopped:

        st.markdown(
            "🟠 **Previous run stopped**"
        )

    elif run_complete:

        st.markdown(
            "🟢 **Quantitative run complete**"
        )

    else:

        st.markdown(
            "🔵 **Compiled**"
        )

    st.divider()

    if st.button(
        "Reset to example defaults",
        use_container_width=True,
    ):

        reset_all()
        st.rerun()


# ==========================================================
# MAIN LOGO
# ==========================================================

render_main_logo()


# ==========================================================
# PAGE ROUTING
# ==========================================================

if st.session_state.get("show_docs", False):

    render_docs_page()

elif page == "Setup":
    render_setup_page()

elif page == "X-ray tube":
    render_tube_page()

elif page == "Detector":
    render_detector_page()

elif page == "Physics":
    render_physics_page()

elif page == "Build & run":
    render_run_page()

elif page == "Results":
    render_results_page()