from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from builder import build_simulation
from components.common import (
    clean_records,
    material_input,
    page_header,
    records_editor,
    save_custom_material,
)
from state import invalidate_simulation


SPECTRUM_UPLOAD_DIR = (
    Path(__file__).resolve().parent.parent
    / "uploads"
    / "spectra"
)


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
        # ==========================================================
        # SPECTRUM SOURCE
        # ==========================================================

        saved_source_mode = tube.get("source_mode", "spekpy")

        source_mode = st.radio(
            "Spectrum source",
            options=["spekpy", "file"],
            index=0 if saved_source_mode == "spekpy" else 1,
            format_func=lambda value: (
                "Generate with SpekPy"
                if value == "spekpy"
                else "Upload spectrum file"
            ),
            horizontal=True,
            key="tube_source_mode",
        )

        # Save the selected source immediately. This is important because
        # the spectrum preview is outside the form and uses cfg directly.
        if source_mode != saved_source_mode:
            tube["source_mode"] = source_mode
            st.session_state.pop("xray_spectrum_preview", None)
            invalidate_simulation()
        else:
            tube["source_mode"] = source_mode

        # UPLOADED SPECTRUM

        uploaded_spectrum = None

        if source_mode == "file":

            st.caption(
                "Upload a two-column spectrum: "
                "energy [keV], intensity [photons/s/keV]."
            )

            uploaded_spectrum = st.file_uploader(
                "Upload or replace spectrum file",
                type=["csv", "txt", "dat"],
                key="tube_spectrum_upload",
            )
            if uploaded_spectrum is not None:

                SPECTRUM_UPLOAD_DIR.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                filename = Path(uploaded_spectrum.name).name

                path = SPECTRUM_UPLOAD_DIR / filename

                # Only rewrite if needed
                uploaded_bytes = uploaded_spectrum.getvalue()

                if (
                    not path.exists()
                    or path.read_bytes() != uploaded_bytes
                ):
                    path.write_bytes(uploaded_bytes)

                tube["spectrum_file_path"] = str(
                    path.resolve()
                )

                tube["spectrum_file_name"] = filename

                invalidate_simulation()

            current_spectrum_name = tube.get(
                "spectrum_file_name"
            )

            current_spectrum_path = tube.get(
                "spectrum_file_path"
            )

            if (
                current_spectrum_name
                and current_spectrum_path
            ):
                st.success(
                    f"Current spectrum: {current_spectrum_name}"
                )

                st.caption(
                    f"Saved at: {current_spectrum_path}"
                )

            else:
                st.info(
                    "No spectrum file is currently loaded."
                )

           


        with st.form("tube_basic_form"):
            name = st.text_input(
                "Tube name",
                value=tube["name"],
            )

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

                anode_options = [
                    "Cr",
                    "Cu",
                    "Mo",
                    "Rh",
                    "Ag",
                    "W",
                    "Au",
                ]

                current_anode = tube.get("anode_symbol", "W")
                if current_anode not in anode_options:
                    current_anode = "W"

                target = c3.selectbox(
                    "Anode",
                    anode_options,
                    index=anode_options.index(current_anode),
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

            submitted = st.form_submit_button(
                "Save tube",
                type="primary",
            )

            if submitted:
                spectrum_path = tube.get("spectrum_file_path")
                spectrum_name = tube.get("spectrum_file_name")

                if source_mode == "file":
                    if not spectrum_path or not spectrum_name:
                        st.error("Please upload a spectrum file.")
                        save_allowed = False
                    elif not Path(spectrum_path).is_file():
                        st.error(
                            "The configured spectrum file no longer "
                            f"exists: {spectrum_path}"
                        )
                        save_allowed = False
                    else:
                        save_allowed = True
                else:
                    save_allowed = True

                if save_allowed:
                    # Keep the uploaded-file path/name even while SpekPy
                    # is selected. source_mode alone decides which source
                    # is active, so switching back to file mode restores
                    # the previously uploaded spectrum.
                    tube.update(
                        {
                            "source_mode": source_mode,
                            "spectrum_file_path": spectrum_path,
                            "spectrum_file_name": spectrum_name,
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
                            "tube_collimator_radius_mm": coll_radius,
                            "elevation_deg": elevation,
                            "azimuth_deg": azimuth,
                        }
                    )

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

                    st.session_state.pop(
                        "xray_spectrum_preview",
                        None,
                    )
                    invalidate_simulation()
                    st.success("Tube saved.")

        # ==========================================================
        # SPECTRUM PREVIEW
        # ==========================================================

        st.divider()

        if st.button(
            "Preview current X-ray tube spectrum",
            key="preview_xray_spectrum",
        ):
            try:
                # The preview uses cfg directly, so make sure the
                # currently selected source is present before building.
                tube["source_mode"] = source_mode

                if source_mode == "file":
                    spectrum_path = tube.get("spectrum_file_path")

                    if not spectrum_path:
                        raise ValueError(
                            "No uploaded spectrum file is configured."
                        )

                    if not Path(spectrum_path).is_file():
                        raise ValueError(
                            "Uploaded spectrum file does not exist: "
                            f"{spectrum_path}"
                        )

                with st.spinner("Generating spectrum..."):
                    preview_simulation = build_simulation(cfg)
                    preview_simulation.compile()

                    energy_mev = preview_simulation.energy_bin
                    fluence = preview_simulation.fluence_list

                if energy_mev is None or fluence is None:
                    raise ValueError(
                        "No spectrum was generated."
                    )

                spectrum_df = pd.DataFrame(
                    {
                        "Energy (keV)": (
                            pd.Series(energy_mev, dtype=float)
                            * 1000.0
                        ),
                        "Intensity": pd.Series(
                            fluence,
                            dtype=float,
                        ),
                    }
                )

                st.session_state[
                    "xray_spectrum_preview"
                ] = spectrum_df

            except Exception as exc:
                st.error(
                    f"Unable to generate spectrum: {exc}"
                )

        # Keep showing the preview on later Streamlit reruns instead
        # of displaying it only during the button-click rerun.
        spectrum_preview = st.session_state.get(
            "xray_spectrum_preview"
        )

        if spectrum_preview is not None:
            st.markdown("### Current X-ray spectrum")

            if source_mode == "file":
                spectrum_name = tube.get("spectrum_file_name")
                if spectrum_name:
                    st.caption(f"Source file: {spectrum_name}")
            else:
                st.caption("Source: SpekPy")

            st.line_chart(
                spectrum_preview,
                x="Energy (keV)",
                y="Intensity",
                height=400,
            )

            with st.expander("View spectrum data"):
                st.dataframe(
                    spectrum_preview,
    width="stretch",
                    hide_index=True,
                )

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
            "Physical filters placed in front of the tube window."
        )

        # ==========================================================
        # FILTER LIST
        # ==========================================================

        rows = records_editor(
            "Tube Geant4 filters",
            tube["geant4_filters"],
            key="tube_geant4_filters_editor",
            column_config={
                "enabled": st.column_config.CheckboxColumn(
                    "Enabled",
                    default=True,
                ),
                "name": st.column_config.TextColumn(
                    "Name"
                ),

                # Hide geometry/material fields from the main table.
                "shape": None,
                "material": None,
                "radius_mm": None,
                "width_mm": None,
                "height_mm": None,
                "thickness_mm": None,
                "distance_mm": None,
            },
        )

        filter_rows = clean_records(
            rows,
            "name",
        )

        selected_index = None
        material = None
        custom_material = None
        material_valid = True

        # ==========================================================
        # SELECTED FILTER EDITOR
        # ==========================================================

        if filter_rows:

            st.divider()

            selected_index = st.selectbox(
                "Select filter",
                options=list(
                    range(len(filter_rows))
                ),
                format_func=lambda i: (
                    str(
                        filter_rows[i].get(
                            "name",
                            "",
                        )
                    ).strip()
                    or f"Filter {i + 1}"
                ),
                key="selected_tube_geant4_filter",
            )

            selected_filter = filter_rows[
                selected_index
            ]

            st.markdown("### Filter geometry")

            # ======================================================
            # SHAPE
            # ======================================================

            shape_options = [
                "Circular",
                "Rectangular",
            ]

            current_shape = selected_filter.get(
                "shape",
                "Circular",
            )

            if current_shape not in shape_options:
                current_shape = "Circular"

            shape = st.selectbox(
                "Shape",
                shape_options,
                index=shape_options.index(
                    current_shape
                ),
                key=(
                    "tube_filter_shape_"
                    f"{selected_index}"
                ),
            )

            # ======================================================
            # CIRCULAR
            # ======================================================

            if shape == "Circular":

                c1, c2, c3 = st.columns(3)

                radius = c1.number_input(
                    "Radius (mm)",
                    min_value=0.000001,
                    value=float(
                        selected_filter.get(
                            "radius_mm",
                            5.0,
                        )
                        or 5.0
                    ),
                    key=(
                        "tube_filter_radius_"
                        f"{selected_index}"
                    ),
                )

                thickness = c2.number_input(
                    "Thickness (mm)",
                    min_value=0.000001,
                    value=float(
                        selected_filter.get(
                            "thickness_mm",
                            0.5,
                        )
                        or 0.5
                    ),
                    key=(
                        "tube_filter_thickness_"
                        f"{selected_index}"
                    ),
                )

                distance = c3.number_input(
                    "Distance from window (mm)",
                    min_value=0.0,
                    value=float(
                        selected_filter.get(
                            "distance_mm",
                            0.0,
                        )
                        or 0.0
                    ),
                    key=(
                        "tube_filter_distance_"
                        f"{selected_index}"
                    ),
                )

                # Keep old values internally, but they are not shown.
                width = selected_filter.get(
                    "width_mm",
                    0.0,
                )

                height = selected_filter.get(
                    "height_mm",
                    0.0,
                )

            # ======================================================
            # RECTANGULAR
            # ======================================================

            else:

                c1, c2 = st.columns(2)

                width = c1.number_input(
                    "Width (mm)",
                    min_value=0.000001,
                    value=float(
                        selected_filter.get(
                            "width_mm",
                            5.0,
                        )
                        or 5.0
                    ),
                    key=(
                        "tube_filter_width_"
                        f"{selected_index}"
                    ),
                )

                height = c2.number_input(
                    "Height (mm)",
                    min_value=0.000001,
                    value=float(
                        selected_filter.get(
                            "height_mm",
                            5.0,
                        )
                        or 5.0
                    ),
                    key=(
                        "tube_filter_height_"
                        f"{selected_index}"
                    ),
                )

                c1, c2 = st.columns(2)

                thickness = c1.number_input(
                    "Thickness (mm)",
                    min_value=0.000001,
                    value=float(
                        selected_filter.get(
                            "thickness_mm",
                            0.5,
                        )
                        or 0.5
                    ),
                    key=(
                        "tube_filter_thickness_"
                        f"{selected_index}"
                    ),
                )

                distance = c2.number_input(
                    "Distance from window (mm)",
                    min_value=0.0,
                    value=float(
                        selected_filter.get(
                            "distance_mm",
                            0.0,
                        )
                        or 0.0
                    ),
                    key=(
                        "tube_filter_distance_"
                        f"{selected_index}"
                    ),
                )

                # Keep old value internally, but it is not shown.
                radius = selected_filter.get(
                    "radius_mm",
                    0.0,
                )

            # ======================================================
            # MATERIAL
            # ======================================================

            st.divider()

            st.markdown("### Filter material")

            current_material = str(
                selected_filter.get(
                    "material",
                    "G4_Al",
                )
                or "G4_Al"
            )

            material, custom_material, material_valid = (
                material_input(
                    label="Material",
                    current_material=current_material,
                    custom_materials=cfg[
                        "custom_materials"
                    ],
                    key=(
                        "tube_geant4_filter_"
                        f"{selected_index}_material"
                    ),
                    default_geant4="G4_Al",
                )
            )

        else:

            st.info(
                "Add a filter row above first."
            )

        # ==========================================================
        # SAVE
        # ==========================================================

        if st.button(
            "Save tube Geant4 filters",
            type="primary",
            key="save_tube_geant4_filters",
            disabled=not material_valid,
        ):

            if selected_index is not None:

                selected_filter = filter_rows[
                    selected_index
                ]

                selected_filter[
                    "shape"
                ] = shape

                selected_filter[
                    "material"
                ] = material

                selected_filter[
                    "radius_mm"
                ] = radius

                selected_filter[
                    "width_mm"
                ] = width

                selected_filter[
                    "height_mm"
                ] = height

                selected_filter[
                    "thickness_mm"
                ] = thickness

                selected_filter[
                    "distance_mm"
                ] = distance

                save_custom_material(
                    cfg["custom_materials"],
                    custom_material,
                )

            # Give new rows basic defaults.
            for row in filter_rows:

                row.setdefault(
                    "shape",
                    "Circular",
                )

                if not str(
                    row.get(
                        "material",
                        "",
                    )
                ).strip():
                    row["material"] = "G4_Al"

                row.setdefault(
                    "radius_mm",
                    5.0,
                )

                row.setdefault(
                    "width_mm",
                    5.0,
                )

                row.setdefault(
                    "height_mm",
                    5.0,
                )

                row.setdefault(
                    "thickness_mm",
                    0.5,
                )

                row.setdefault(
                    "distance_mm",
                    0.0,
                )

            tube["geant4_filters"] = (
                filter_rows
            )

            invalidate_simulation()

            st.success(
                "Tube Geant4 filters saved."
            )