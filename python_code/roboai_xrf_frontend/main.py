import base64
from pathlib import Path

import streamlit as st

from theme import apply_roboai_libs_theme
from state import (
    configuration_fingerprint,
    init_state,
    reset_all,
    update_geant4_process_state,
)

from components.setup_page import render_setup_page
from components.tube_page import render_tube_page
from components.detector_page import render_detector_page
from components.physics_page import render_physics_page
from components.run_page import render_run_page
from components.results_page import render_results_page
from components.docs_page import render_docs_page


st.set_page_config(
    page_title="RoboAI XRF",
    page_icon="⚛",
    layout="wide",
    initial_sidebar_state="expanded",
)


BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "roboai_logo.png"


PAGES = {
    "Setup": render_setup_page,
    "X-ray tube": render_tube_page,
    "Detector": render_detector_page,
    "Physics": render_physics_page,
    "Build & run": render_run_page,
    "Results": render_results_page,
}


@st.cache_data
def _logo_base64() -> str:
    return base64.b64encode(
        LOGO_PATH.read_bytes()
    ).decode("utf-8")


def render_logo(css_class: str) -> None:
    st.markdown(
        f"""
        <div class="{css_class}">
            <img
                src="data:image/png;base64,{_logo_base64()}"
                alt="RoboAI"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )


def _open_docs() -> None:
    st.session_state.show_docs = True


def _leave_docs() -> None:
    st.session_state.show_docs = False


def _render_active_configuration() -> None:
    st.caption("Active configuration")

    loaded_name = st.session_state.loaded_config_name
    imported = st.session_state.config_was_imported

    if imported and loaded_name:
        st.markdown(f"**📄 {loaded_name}**")
        st.caption("Imported RoboAI configuration")
        return

    st.markdown("**Example defaults**")
    st.caption("Using frontend default configuration")


def _simulation_is_current() -> bool:
    simulation = st.session_state.simulation
    compiled_fingerprint = st.session_state.compiled_fingerprint

    if simulation is None or compiled_fingerprint is None:
        return False

    return (
        compiled_fingerprint
        == configuration_fingerprint(
            st.session_state.ui_config
        )
    )


def _render_simulation_status() -> None:
    st.caption("Simulation status")

    simulation = st.session_state.simulation

    if st.session_state.geant4_running:
        process = st.session_state.geant4_process

        if process is not None:
            st.markdown(
                f"🟣 **Running** · PID {process.pid}"
            )
        else:
            st.markdown("🟣 **Running**")

        return

    if simulation is None:
        st.markdown("⚪ **Not compiled**")
        return

    if not _simulation_is_current():
        st.markdown("🟡 **Configuration changed**")
        st.caption(
            "Build & compile again before running."
        )
        return

    if st.session_state.geant4_stopped:
        st.markdown("🟠 **Previous run stopped**")
        return

    if st.session_state.run_complete:
        st.markdown("🟢 **Quantitative run complete**")
        return

    st.markdown("🔵 **Compiled**")


def _render_sidebar() -> str:
    with st.sidebar:
        render_logo("roboai-sidebar-logo")

        st.markdown(
            '<div class="sidebar-product-name">'
            "XRF Simulation"
            "</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            "Geant4 XRF simulation interface"
        )

        st.button(
            "Documentation",
            use_container_width=True,
            key="open_documentation",
            on_click=_open_docs,
        )

        st.divider()

        page = st.radio(
            "Navigation",
            options=list(PAGES),
            label_visibility="collapsed",
            key="navigation_page",
            on_change=_leave_docs,
        )

        st.divider()

        _render_active_configuration()

        st.divider()

        _render_simulation_status()

        st.divider()

        st.button(
            "Reset to example defaults",
            use_container_width=True,
            on_click=reset_all,
        )

    return page


def main() -> None:
    apply_roboai_libs_theme()
    init_state()

    # Refresh subprocess state whenever Streamlit reruns.
    update_geant4_process_state()

    page = _render_sidebar()

    render_logo("roboai-main-logo")

    if st.session_state.show_docs:
        render_docs_page()
        return

    PAGES[page]()


if __name__ == "__main__":
    main()