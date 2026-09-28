from __future__ import annotations

import json

import streamlit as st

from components.common import (
    material_input,
    page_header,
    save_custom_material,
)

from state import (
    RoboAIConfigValidationError,
    invalidate_simulation,
    load_uploaded_config,
    validate_roboaixrf_config,
)


def render_setup_page():
    cfg = st.session_state.ui_config

    # ==========================================================
    # PAGE HEADER
    # ==========================================================

    page_header(
        "Simulation setup",
        "Configure the world and sample. "
        "Custom materials can be created and managed "
        "directly from any material selector.",
    )

    # ==========================================================
    # ACTIVE CONFIGURATION
    # ==========================================================

    loaded_name = st.session_state.get(
        "loaded_config_name"
    )

    if loaded_name:
        st.success(
            f"Active configuration: {loaded_name}",
            icon="✅",
        )
    else:
        st.info(
            "Using the default configuration. "
            "You can edit it manually or import an "
            "existing config.json."
        )

    # ==========================================================
    # IMPORT EXISTING CONFIGURATION
    # ==========================================================

    with st.expander(
        "Import existing configuration",
        expanded=False,
    ):
        st.caption(
            "Only config.json files generated in the "
            "RoboAI XRF format are accepted. Missing or "
            "misspelled required keys are rejected; they "
            "are never replaced silently with example defaults."
        )

        uploaded_file = st.file_uploader(
            "Upload config.json",
            type=["json"],
            key="config_json_upload",
        )

        if uploaded_file is not None:
            try:
                uploaded_config = json.loads(
                    uploaded_file
                    .getvalue()
                    .decode("utf-8-sig")
                )

                format_is_valid = True
                validation_message = None

                try:
                    validate_roboaixrf_config(
                        uploaded_config
                    )
                except RoboAIConfigValidationError as exc:
                    format_is_valid = False
                    validation_message = str(exc)

                c1, c2 = st.columns(
                    [2, 1]
                )

                with c1:
                    st.write(
                        "**Selected:** "
                        f"{uploaded_file.name}"
                    )

                    if format_is_valid:
                        st.success(
                            "RoboAI config structure and "
                            "required keys are valid."
                        )
                    else:
                        st.error(
                            validation_message
                        )

                with c2:
                    if st.button(
                        "Load configuration",
                        type="primary",
                        width="stretch",
                        key=(
                            "load_uploaded_"
                            "config_button"
                        ),
                        disabled=not format_is_valid,
                    ):
                        load_uploaded_config(
                            uploaded_config,
                            filename=(
                                uploaded_file.name
                            ),
                        )

                        st.toast(
                            "Configuration loaded.",
                            icon="✅",
                        )

                        st.rerun()

                with st.expander(
                    "Preview uploaded JSON",
                    expanded=False,
                ):
                    st.json(
                        uploaded_config
                    )

            except json.JSONDecodeError as exc:
                st.error(
                    f"Invalid JSON file: {exc}"
                )

            except UnicodeDecodeError as exc:
                st.error(
                    "The uploaded file is not valid "
                    f"UTF-8 JSON: {exc}"
                )

            except Exception as exc:
                st.error(
                    f"Configuration rejected: {exc}"
                )

    # ==========================================================
    # VIEW CURRENT IMPORTED FILE
    # ==========================================================

    active_raw_config = st.session_state.get(
        "uploaded_config_raw"
    )

    if active_raw_config is not None:
        with st.expander(
            "View active imported configuration",
            expanded=False,
        ):
            st.json(
                active_raw_config
            )

    st.divider()

    # Uploading a configuration may replace ui_config.
    cfg = st.session_state.ui_config

    # ==========================================================
    # SETUP TABS
    # ==========================================================

    tab_world, tab_sample = st.tabs(
        [
            "World",
            "Sample",
        ]
    )

    # ==========================================================
    # WORLD
    # ==========================================================

    with tab_world:
        world = cfg["world"]

        (
            material,
            custom_material,
            material_valid,
        ) = material_input(
            label="World material",
            current_material=world["material"],
            custom_materials=cfg[
                "custom_materials"
            ],
            key="world_material",
            default_geant4="G4_Galactic",
        )

        c1, c2, c3 = st.columns(3)

        sx = c1.number_input(
            "World X (mm)",
            min_value=0.001,
            value=float(
                world["size_x_mm"]
            ),
        )

        sy = c2.number_input(
            "World Y (mm)",
            min_value=0.001,
            value=float(
                world["size_y_mm"]
            ),
        )

        sz = c3.number_input(
            "World Z (mm)",
            min_value=0.001,
            value=float(
                world["size_z_mm"]
            ),
        )

        if st.button(
            "Save world",
            type="primary",
            key="save_world",
            disabled=not material_valid,
        ):
            save_custom_material(
                cfg["custom_materials"],
                custom_material,
            )

            world.update(
                {
                    "material": material,
                    "size_x_mm": sx,
                    "size_y_mm": sy,
                    "size_z_mm": sz,
                }
            )

            invalidate_simulation()

            st.success(
                "World saved."
            )

    # ==========================================================
    # SAMPLE
    # ==========================================================

    with tab_sample:
        sample = cfg["sample"]

        c1, c2 = st.columns(2)

        name = c1.text_input(
            "Sample name",
            value=sample["name"],
        )

        shape_options = [
            "Rectangular",
            "Circular",
        ]

        current_shape = sample.get(
            "shape",
            "Rectangular",
        )

        if current_shape not in shape_options:
            current_shape = "Rectangular"

        shape = c2.selectbox(
            "Shape",
            shape_options,
            index=shape_options.index(
                current_shape
            ),
        )

        (
            material,
            custom_material,
            material_valid,
        ) = material_input(
            label="Sample material",
            current_material=sample["material"],
            custom_materials=cfg[
                "custom_materials"
            ],
            key="sample_material",
            default_geant4="G4_Fe",
        )

        # ======================================================
        # RECTANGULAR SAMPLE
        # ======================================================

        if shape == "Rectangular":
            c1, c2, c3 = st.columns(3)

            width = c1.number_input(
                "Width (mm)",
                min_value=0.000001,
                value=float(
                    sample.get(
                        "width_mm",
                        10.0,
                    )
                ),
            )

            height = c2.number_input(
                "Height (mm)",
                min_value=0.000001,
                value=float(
                    sample.get(
                        "height_mm",
                        10.0,
                    )
                ),
            )

            thickness = c3.number_input(
                "Thickness (mm)",
                min_value=0.000001,
                value=float(
                    sample.get(
                        "thickness_mm",
                        0.1,
                    )
                ),
                format="%.6f",
            )

            radius = sample.get(
                "radius_mm",
                5.0,
            )

        # ======================================================
        # CIRCULAR SAMPLE
        # ======================================================

        else:
            c1, c2 = st.columns(2)

            radius = c1.number_input(
                "Radius (mm)",
                min_value=0.000001,
                value=float(
                    sample.get(
                        "radius_mm",
                        5.0,
                    )
                ),
            )

            thickness = c2.number_input(
                "Thickness (mm)",
                min_value=0.000001,
                value=float(
                    sample.get(
                        "thickness_mm",
                        0.1,
                    )
                ),
                format="%.6f",
            )

            width = sample.get(
                "width_mm",
                10.0,
            )

            height = sample.get(
                "height_mm",
                10.0,
            )

        # ======================================================
        # SAVE SAMPLE
        # ======================================================

        if st.button(
            "Save sample",
            type="primary",
            key="save_sample",
            disabled=not material_valid,
        ):
            save_custom_material(
                cfg["custom_materials"],
                custom_material,
            )

            sample.update(
                {
                    "name": name.strip(),
                    "material": material,
                    "shape": shape,
                    "width_mm": width,
                    "height_mm": height,
                    "radius_mm": radius,
                    "thickness_mm": thickness,
                }
            )

            invalidate_simulation()

            st.success(
                "Sample saved."
            )
