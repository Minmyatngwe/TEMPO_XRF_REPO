from __future__ import annotations

import streamlit as st

from components.common import page_header, records_editor, clean_records
from state import invalidate_simulation


def render_tube_page():
    cfg = st.session_state.ui_config
    tube = cfg["tube"]

    page_header(
        "X-ray tube",
        "Tube operating parameters, placement, window, SpekPy filtration, and optional physical Geant4 filters.",
    )

    tab_basic, tab_window, tab_spekpy, tab_geant4 = st.tabs(
        ["Tube", "Window", "SpekPy filters", "Geant4 filters"]
    )

    with tab_basic:
        with st.form("tube_basic_form"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Tube name", value=tube["name"])
            voltage = c2.number_input(
                "Voltage (kV)", min_value=1.0, value=float(tube["voltage_kv"])
            )
            current = c3.number_input(
                "Current (mA)", min_value=0.000001, value=float(tube["current_ma"])
            )

            c1, c2, c3 = st.columns(3)
            target = c1.selectbox(
                "Anode",
                ["Cr", "Cu", "Mo", "Rh", "Ag", "W", "Au"],
                index=["Cr", "Cu", "Mo", "Rh", "Ag", "W", "Au"].index(
                    tube["anode_symbol"]
                ),
            )
            angle = c2.number_input(
                "Anode angle (deg)", value=float(tube["anode_angle_deg"])
            )
            focal = c3.number_input(
                "Focal spot diameter (mm)",
                min_value=0.000001,
                value=float(tube["focal_spot_diameter_mm"]),
                format="%.6f",
            )

            c1, c2, c3 = st.columns(3)
            source_sample = c1.number_input(
                "Focal spot → sample (mm)",
                min_value=0.000001,
                value=float(tube["focal_spot_to_sample_distance_mm"]),
            )
            window_sample = c2.number_input(
                "Window → sample (mm)",
                min_value=0.000001,
                value=float(tube["tube_window_to_sample_distance_mm"]),
            )
            window_coll = c3.number_input(
                "Window → virtual collimator (mm)",
                min_value=0.0,
                value=float(tube["tube_window_to_virtual_collimator_distance_mm"]),
            )

            c1, c2, c3 = st.columns(3)
            coll_radius = c1.number_input(
                "Virtual collimator radius (mm)",
                min_value=0.000001,
                value=float(tube["tube_collimator_radius_mm"]),
                format="%.6f",
            )
            elevation = c2.number_input(
                "Elevation (deg)", value=float(tube["elevation_deg"])
            )
            azimuth = c3.number_input(
                "Azimuth (deg)", value=float(tube["azimuth_deg"])
            )

            c1, c2 = st.columns(2)
            tube_type = c1.selectbox(
                "Tube type",
                ["reflection", "transmission"],
                index=0 if tube["tube_type"] == "reflection" else 1,
            )
            target_thickness = c2.number_input(
                "Target thickness (µm)",
                min_value=0.0,
                value=float(tube["target_thickness_um"]),
            )

            if st.form_submit_button("Save tube", type="primary"):
                tube.update(
                    {
                        "name": name.strip(),
                        "voltage_kv": voltage,
                        "current_ma": current,
                        "anode_symbol": target,
                        "anode_angle_deg": angle,
                        "focal_spot_diameter_mm": focal,
                        "focal_spot_to_sample_distance_mm": source_sample,
                        "tube_window_to_sample_distance_mm": window_sample,
                        "tube_window_to_virtual_collimator_distance_mm": window_coll,
                        "tube_collimator_radius_mm": coll_radius,
                        "elevation_deg": elevation,
                        "azimuth_deg": azimuth,
                        "tube_type": tube_type,
                        "target_thickness_um": target_thickness,
                    }
                )
                invalidate_simulation()
                st.success("Tube saved.")

    with tab_window:
        window = tube["window"]
        with st.form("tube_window_form"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Window name", value=window["name"])
            material = c2.text_input("Window material", value=window["material"])
            thickness = c3.number_input(
                "Window thickness (mm)",
                min_value=0.0000001,
                value=float(window["thickness_mm"]),
                format="%.7f",
            )
            if st.form_submit_button("Save window", type="primary"):
                window.update(
                    {
                        "name": name.strip(),
                        "material": material.strip(),
                        "thickness_mm": thickness,
                    }
                )
                invalidate_simulation()
                st.success("Tube window saved.")

    with tab_spekpy:
        st.caption("These filters modify the SpekPy source spectrum.")
        rows = records_editor(
            "SpekPy filters",
            tube["spekpy_filters"],
            key="spekpy_filters_editor",
            column_config={
                "element": st.column_config.TextColumn("Element"),
                "thickness_mm": st.column_config.NumberColumn(
                    "Thickness (mm)", min_value=0.0, format="%.6f"
                ),
            },
        )
        if st.button("Save SpekPy filters", type="primary"):
            tube["spekpy_filters"] = clean_records(rows, "element")
            invalidate_simulation()
            st.success("SpekPy filters saved.")

    with tab_geant4:
        st.caption(
            "Physical filters placed in front of the tube window. "
            "For Circular rows use radius_mm; for Rectangular rows use width_mm and height_mm."
        )
        rows = records_editor(
            "Tube Geant4 filters",
            tube["geant4_filters"],
            key="tube_geant4_filters_editor",
            column_config={
                "enabled": st.column_config.CheckboxColumn("Enabled", default=True),
                "name": st.column_config.TextColumn("Name"),
                "shape": st.column_config.SelectboxColumn(
                    "Shape", options=["Circular", "Rectangular"]
                ),
                "material": st.column_config.TextColumn("Material"),
                "radius_mm": st.column_config.NumberColumn("Radius (mm)", min_value=0.0),
                "width_mm": st.column_config.NumberColumn("Width (mm)", min_value=0.0),
                "height_mm": st.column_config.NumberColumn("Height (mm)", min_value=0.0),
                "thickness_mm": st.column_config.NumberColumn(
                    "Thickness (mm)", min_value=0.0
                ),
                "distance_mm": st.column_config.NumberColumn(
                    "Distance from window (mm)", min_value=0.0
                ),
            },
        )
        if st.button("Save tube Geant4 filters", type="primary"):
            tube["geant4_filters"] = clean_records(rows, "name")
            invalidate_simulation()
            st.success("Tube Geant4 filters saved.")
