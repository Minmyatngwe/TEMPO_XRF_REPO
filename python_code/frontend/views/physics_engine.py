import streamlit as st
import json
from views.physics_state import build_physics_config,reset_physics_defaults


st.title("Physics Settings")

st.subheader("Atomic De-excitation")

fluorescence = st.toggle(
    "Fluorescence",
    key="physics_fluorescence",
    help="Generate characteristic X-rays following atomic vacancies.",
)

auger = st.toggle(
    "Auger electrons",
    key="physics_auger",
)

pixe = st.toggle(
    "PIXE",
    key="physics_pixe",
)

ignore_deexcitation_cut = st.toggle(
    "Ignore production cuts for atomic de-excitation",
    key="physics_ignore_deexcitation_cut",
)

if ignore_deexcitation_cut:
    st.info(
        "Fluorescence photons and Auger electrons can be generated even "
        "when they are below the normal production threshold. Normal "
        "secondary production still uses the region cuts."
    )


st.subheader("Variance Reduction")

secondary_splitting_on = st.toggle(
    "Use secondary splitting",
    key="physics_secondary_splitting_on",
)

if secondary_splitting_on:
    with st.expander("Secondary splitting settings", expanded=False):

        phot_splitting = st.number_input(
            "Photoelectric splitting factor",
            min_value=1,
            step=1,
            key="physics_phot_splitting",
            help="Number of weighted statistical alternatives.",
        )

        compt_splitting = st.number_input(
            "Compton splitting factor",
            min_value=1,
            step=1,
            key="physics_compt_splitting",
        )

        rayl_splitting = st.number_input(
            "Rayleigh splitting factor",
            min_value=1,
            step=1,
            key="physics_rayl_splitting",
        )

        splitting_max_energy_kev = st.number_input(
            "Maximum splitting energy",
            min_value=0.001,
            step=1.0,
            format="%.3f",
            key="physics_splitting_max_energy_kev",
        )

        st.caption("Energy unit: keV")


interaction_bias_on = st.toggle(
    "Use interaction biasing",
    key="physics_interaction_bias_on",
)


with st.expander("Advanced settings", expanded=False):
    st.subheader("SampleRegion production cuts")

    gamma_cut_mm = st.number_input(
        "Gamma cut",
        min_value=0.0,
        step=0.0001,
        format="%.6f",
        key="physics_sample_gamma_cut_mm",
    )

    electron_cut_mm = st.number_input(
        "Electron cut",
        min_value=0.0,
        step=0.001,
        format="%.6f",
        key="physics_sample_electron_cut_mm",
    )

    positron_cut_mm = st.number_input(
        "Positron cut",
        min_value=0.0,
        step=0.001,
        format="%.6f",
        key="physics_sample_positron_cut_mm",
    )

    proton_cut_mm = st.number_input(
        "Proton cut",
        min_value=0.0,
        step=0.001,
        format="%.6f",
        key="physics_sample_proton_cut_mm",
    )
    flu_dataset=st.selectbox(
        "Flu Dataset",
        ["Bearden", "ANSTO", "RoboAI"],
        index=2,
        key="physics_flu_dataset"
    )   
    st.caption("Production-cut unit: mm")


st.button(
    "Reset physics settings to defaults",
    on_click=reset_physics_defaults,
)


physics_config = build_physics_config()

st.session_state["physics_config"] = physics_config