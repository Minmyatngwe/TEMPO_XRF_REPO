from __future__ import annotations

import streamlit as st

from components.common import page_header, records_editor, clean_records
from state import invalidate_simulation
from pathlib import Path




SPECTRUM_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "spectra"


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

        source_mode = st.radio(
            "Spectrum source",
            options=["spekpy", "file"],
            index=0 if tube.get("source_mode", "spekpy") == "spekpy" else 1,
            format_func=lambda value: (
                "Generate with SpekPy"
                if value == "spekpy"
                else "Upload spectrum file"
            ),
            horizontal=True,
        )

        # --------------------------------------------------
        # Uploaded spectrum
        # --------------------------------------------------

        uploaded_spectrum = None

        if source_mode == "file":
            st.caption(
                "Upload a two-column spectrum: "
                "energy [keV], intensity [photons/s/keV]."
            )

            uploaded_spectrum = st.file_uploader(
                "Spectrum file",
                type=["csv", "txt", "dat"],
                key="tube_spectrum_upload",
            )

            if tube.get("spectrum_file_name"):
                st.caption(
                    f"Current file: {tube['spectrum_file_name']}"
                )

        # --------------------------------------------------
        # Tube form
        # --------------------------------------------------

        with st.form("tube_basic_form"):

            name = st.text_input(
                "Tube name",
                value=tube["name"],
            )

            # ==============================================
            # SPEKPY ONLY
            # ==============================================

            if source_mode == "spekpy":

                c1, c2, c3 = st.columns(3)

                voltage = c1.number_input(
                    "Voltage (kV)",
                    min_value=1.0,
                    value=float(tube["voltage_kv"]),
                )

                current = c2.number_input(
                    "Current (mA)",
                    min_value=0.000001,
                    value=float(tube["current_ma"]),
                )

                target = c3.selectbox(
                    "Anode",
                    ["Cr", "Cu", "Mo", "Rh", "Ag", "W", "Au"],
                    index=[
                        "Cr",
                        "Cu",
                        "Mo",
                        "Rh",
                        "Ag",
                        "W",
                        "Au",
                    ].index(tube["anode_symbol"]),
                )

                c1, c2 = st.columns(2)

                angle = c1.number_input(
                    "Anode angle (deg)",
                    value=float(tube["anode_angle_deg"]),
                )

                tube_type = c2.selectbox(
                    "Tube type",
                    ["reflection", "transmission"],
                    index=(
                        0
                        if tube["tube_type"] == "reflection"
                        else 1
                    ),
                )

                if tube_type == "transmission":
                    target_thickness = st.number_input(
                        "Target thickness (µm)",
                        min_value=0.0,
                        value=float(
                            tube["target_thickness_um"]
                        ),
                    )
                else:
                    target_thickness = 0.0

            # ==============================================
            # COMMON GEOMETRY
            # ==============================================

            c1, c2, c3 = st.columns(3)

            focal = c1.number_input(
                "Focal spot diameter (mm)",
                min_value=0.000001,
                value=float(
                    tube["focal_spot_diameter_mm"]
                ),
                format="%.6f",
            )

            source_sample = c2.number_input(
                "Focal spot → sample (mm)",
                min_value=0.000001,
                value=float(
                    tube[
                        "focal_spot_to_sample_distance_mm"
                    ]
                ),
            )

            window_sample = c3.number_input(
                "Window → sample (mm)",
                min_value=0.000001,
                value=float(
                    tube[
                        "tube_window_to_sample_distance_mm"
                    ]
                ),
            )

            c1, c2, c3 = st.columns(3)

            window_coll = c1.number_input(
                "Window → virtual collimator (mm)",
                min_value=0.0,
                value=float(
                    tube[
                        "tube_window_to_virtual_collimator_distance_mm"
                    ]
                ),
            )

            coll_radius = c2.number_input(
                "Virtual collimator radius (mm)",
                min_value=0.000001,
                value=float(
                    tube["tube_collimator_radius_mm"]
                ),
                format="%.6f",
            )

            elevation = c3.number_input(
                "Elevation (deg)",
                value=float(tube["elevation_deg"]),
            )

            azimuth = st.number_input(
                "Azimuth (deg)",
                value=float(tube["azimuth_deg"]),
            )

            # ==============================================
            # SAVE
            # ==============================================

            submitted = st.form_submit_button(
                "Save tube",
                type="primary",
            )

            if submitted:

                # ------------------------------------------
                # File spectrum validation
                # ------------------------------------------

                if (
                    source_mode == "file"
                    and uploaded_spectrum is None
                    and not tube.get("spectrum_file_path")
                ):
                    st.error(
                        "Please upload a spectrum file."
                    )

                else:

                    spectrum_path = tube.get(
                        "spectrum_file_path"
                    )

                    spectrum_name = tube.get(
                        "spectrum_file_name"
                    )

                    # --------------------------------------
                    # Save uploaded file
                    # --------------------------------------

                    if (
                        source_mode == "file"
                        and uploaded_spectrum is not None
                    ):

                        SPECTRUM_UPLOAD_DIR.mkdir(
                            parents=True,
                            exist_ok=True,
                        )

                        filename = Path(
                            uploaded_spectrum.name
                        ).name

                        path = (
                            SPECTRUM_UPLOAD_DIR
                            / filename
                        )

                        path.write_bytes(
                            uploaded_spectrum.getvalue()
                        )

                        spectrum_path = str(
                            path.resolve()
                        )

                        spectrum_name = filename

                    # --------------------------------------
                    # Common values
                    # --------------------------------------

                    tube.update(
                        {
                            "source_mode": source_mode,
                            "spectrum_file_path": (
                                spectrum_path
                                if source_mode == "file"
                                else None
                            ),
                            "spectrum_file_name": (
                                spectrum_name
                                if source_mode == "file"
                                else None
                            ),
                            "name": name.strip(),
                            "focal_spot_diameter_mm": focal,
                            "focal_spot_to_sample_distance_mm": (
                                source_sample
                            ),
                            "tube_window_to_sample_distance_mm": (
                                window_sample
                            ),
                            "tube_window_to_virtual_collimator_distance_mm": (
                                window_coll
                            ),
                            "tube_collimator_radius_mm": (
                                coll_radius
                            ),
                            "elevation_deg": elevation,
                            "azimuth_deg": azimuth,
                        }
                    )

                    # --------------------------------------
                    # SpekPy values
                    # --------------------------------------

                    if source_mode == "spekpy":
                        tube.update(
                            {
                                "voltage_kv": voltage,
                                "current_ma": current,
                                "anode_symbol": target,
                                "anode_angle_deg": angle,
                                "tube_type": tube_type,
                                "target_thickness_um": (
                                    target_thickness
                                ),
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
