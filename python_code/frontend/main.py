import streamlit as st

from copy import deepcopy
from views.physics_state import initialize_physics_state


st.title("ROBOAI XRF SIMULATION")


# =========================================================================
# WIDGETS THAT SHOULD SURVIVE PAGE CHANGES
# =========================================================================

PERSISTENT_WIDGET_PREFIXES = (
    "xray_",
    "world_",
    "use_tube_",
    "number_of_tube_",
    "tube_filter_",
    "sample_",
    "source_",
    "use_detector_",
    "number_of_detector_",
    "detector_",
    "json_",
    "physics_",
    "simulation_",
    "spekpy_",
)


# Some persistent values do not use one of the prefixes above.
PERSISTENT_WIDGET_KEYS = {
    "saved_spekpy_filters",
}


# Widgets whose Session State must NOT be manually assigned.
NON_ASSIGNABLE_WIDGET_KEYS = {
    "spekpy_filter_dataframe",
    "_spekpy_filter_editor",

    # Old uploader keys, in case they still exist in Session State.
    "simulation_json_uploader",
    "simulation_json_uploader_widget",
    "simulation_json_upload",
}


# This is NOT a widget key.
# It is only a permanent backup of widget values.
WIDGET_BACKUP_KEY = "_persistent_widget_state_backup"


# =========================================================================
# HELPERS
# =========================================================================

def should_preserve_widget(key: str) -> bool:

    if key == WIDGET_BACKUP_KEY:
        return False

    if key.endswith("_composition"):
        return False

    if key in NON_ASSIGNABLE_WIDGET_KEYS:
        return False

    if key in PERSISTENT_WIDGET_KEYS:
        return True

    return key.startswith(
        PERSISTENT_WIDGET_PREFIXES
    )


def safe_copy(value):

    try:
        return deepcopy(value)

    except Exception:
        return value


def preserve_widget_state() -> None:
    """
    Preserve input widget values even when their page is not rendered.

    Important:
    - Original widget key names are NOT changed.
    - The backup dictionary is normal application state.
    """

    backup = st.session_state.get(
        WIDGET_BACKUP_KEY,
        {},
    )

    # ---------------------------------------------------------------------
    # STEP 1
    #
    # Restore values that Streamlit may have removed because their widgets
    # were not rendered on the previous page/run.
    # ---------------------------------------------------------------------

    for key, value in tuple(
        backup.items()
    ):

        if key not in st.session_state:

            st.session_state[key] = safe_copy(
                value
            )

    # ---------------------------------------------------------------------
    # STEP 2
    #
    # Store the latest values.
    #
    # When the user changes a widget, Streamlit updates Session State before
    # this app rerun begins, so this catches the newest value.
    # ---------------------------------------------------------------------

    for key in tuple(
        st.session_state.keys()
    ):

        if not should_preserve_widget(
            key
        ):
            continue

        value = st.session_state[
            key
        ]

        backup[key] = safe_copy(
            value
        )

        # Interrupt Streamlit widget cleanup.
        st.session_state[key] = value

    st.session_state[
        WIDGET_BACKUP_KEY
    ] = backup


# =========================================================================
# INITIALIZE
# =========================================================================

initialize_physics_state()

preserve_widget_state()


# =========================================================================
# NAVIGATION
# =========================================================================

pages = [

    st.Page(
        "views/xray_tube.py",
        title="Xray Tube",
    ),

    st.Page(
        "views/geometry.py",
        title="3D-Geometry",
    ),

    st.Page(
        "views/simulation.py",
        title="Start Simulation",
    ),

    st.Page(
        "views/result_and_detector_noise.py",
        title="Detector noise",
    ),

    st.Page(
        "views/physics_engine.py",
        title="Physics Engine",
    ),

    st.Page(
        "views/geometry_supported.py",
        title="Geometry supported shape",
    ),
]


navigation = st.navigation(
    pages
)

navigation.run()