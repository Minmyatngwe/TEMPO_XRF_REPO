from __future__ import annotations

import streamlit as st

from components.common import page_header
from state import invalidate_simulation


def render_physics_page():
    cfg = st.session_state.ui_config
    physics = cfg["physics"]

    page_header(
        "Physics",
        "These fields map directly to roboaixrf.config.physics_engine.Physics.",
    )

    with st.form("physics_form"):
        c1, c2 = st.columns(2)
        interaction_bias = c1.checkbox(
            "Interaction biasing", value=physics["interaction_bias_use"]
        )
        secondary_splitting = c2.checkbox(
            "Secondary splitting", value=physics["secondary_splitting_use"]
        )

        c1, c2, c3, c4 = st.columns(4)
        flu = c1.checkbox("Fluorescence", value=physics["flu_use"])
        auger = c2.checkbox("Auger", value=physics["auger_use"])
        pixe = c3.checkbox("PIXE", value=physics["pixe_use"])
        ignore_cut = c4.checkbox("Ignore cuts", value=physics["ignore_cut_use"])

        c1, c2 = st.columns(2)
        dataset_options = ["ANSTO", "Bearden", "XDB_EADL", "ROBOAI"]
        current_dataset = physics["flu_dataset_name"]
        if current_dataset not in dataset_options:
            dataset_options.append(current_dataset)

        dataset = c1.selectbox(
            "Fluorescence dataset",
            dataset_options,
            index=dataset_options.index(current_dataset),
        )
        maximum_energy = c2.number_input(
            "Maximum energy",
            min_value=0.0,
            value=float(physics["maximum_energy"]),
        )

        c1, c2, c3 = st.columns(3)
        phot = c1.number_input(
            "Photoelectric factor",
            min_value=1,
            value=int(physics["phot_factor"]),
            step=1,
        )
        compt = c2.number_input(
            "Compton factor",
            min_value=1,
            value=int(physics["compt_factor"]),
            step=1,
        )
        rayl = c3.number_input(
            "Rayleigh factor",
            min_value=1,
            value=int(physics["rayl_factor"]),
            step=1,
        )

        c1, c2, c3, c4 = st.columns(4)
        electron_cut = c1.number_input(
            "Electron cut",
            min_value=0.0,
            value=float(physics["electron_cut"]),
            format="%.6f",
        )
        gamma_cut = c2.number_input(
            "Gamma cut",
            min_value=0.0,
            value=float(physics["gamma_cut"]),
            format="%.6f",
        )
        positron_cut = c3.number_input(
            "Positron cut",
            min_value=0.0,
            value=float(physics["positron_cut"]),
            format="%.6f",
        )
        proton_cut = c4.number_input(
            "Proton cut",
            min_value=0.0,
            value=float(physics["proton_cut"]),
            format="%.6f",
        )

        if st.form_submit_button("Save physics", type="primary"):
            physics.update(
                {
                    "interaction_bias_use": interaction_bias,
                    "secondary_splitting_use": secondary_splitting,
                    "flu_use": flu,
                    "auger_use": auger,
                    "pixe_use": pixe,
                    "ignore_cut_use": ignore_cut,
                    "flu_dataset_name": dataset,
                    "maximum_energy": maximum_energy,
                    "phot_factor": int(phot),
                    "compt_factor": int(compt),
                    "rayl_factor": int(rayl),
                    "electron_cut": electron_cut,
                    "gamma_cut": gamma_cut,
                    "positron_cut": positron_cut,
                    "proton_cut": proton_cut,
                }
            )
            invalidate_simulation()
            st.success("Physics saved.")
