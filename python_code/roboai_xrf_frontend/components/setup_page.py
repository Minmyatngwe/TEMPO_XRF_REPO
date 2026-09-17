from __future__ import annotations

import json
import streamlit as st

from components.common import (
    page_header,
    section_title,
    records_editor,
    clean_records,
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
        "Configure the world, reusable materials, and sample. "
        "You can also import an existing RoboAI XRF configuration.",
    )

    # ==========================================================
    # ACTIVE CONFIGURATION
    # ==========================================================

    loaded_name = st.session_state.get("loaded_config_name")

    if loaded_name:
        st.success(
            f"Active configuration: {loaded_name}",
            icon="✅",
        )
    else:
        st.info(
            "Using the default configuration. "
            "You can edit it manually or import an existing config.json."
        )

    # ==========================================================
    # IMPORT EXISTING CONFIGURATION
    # ==========================================================

    with st.expander(
        "Import existing configuration",
        expanded=False,
    ):

        st.caption(
            "Only config.json files generated in the RoboAI XRF format are "
            "accepted. Missing or misspelled required keys are rejected; "
            "they are never replaced silently with example defaults."
        )

        uploaded_file = st.file_uploader(
            "Upload config.json",
            type=["json"],
            key="config_json_upload",
        )

        if uploaded_file is not None:

            try:
                # getvalue() is stable across Streamlit reruns; using json.load
                # directly on the UploadedFile can leave its file pointer at EOF.
                uploaded_config = json.loads(
                    uploaded_file.getvalue().decode("utf-8-sig")
                )

                format_is_valid = True
                validation_message = None

                try:
                    validate_roboaixrf_config(uploaded_config)
                except RoboAIConfigValidationError as exc:
                    format_is_valid = False
                    validation_message = str(exc)

                c1, c2 = st.columns([2, 1])

                with c1:
                    st.write(
                        f"**Selected:** {uploaded_file.name}"
                    )

                    if format_is_valid:
                        st.success(
                            "RoboAI config structure and required keys are valid."
                        )
                    else:
                        st.error(validation_message)

                with c2:
                    if st.button(
                        "Load configuration",
                        type="primary",
                        use_container_width=True,
                        key="load_uploaded_config_button",
                        disabled=not format_is_valid,
                    ):

                        # load_uploaded_config performs a second strict check,
                        # converts every supported RoboAI field to ui_config,
                        # dry-builds the RoboAI objects, and only then replaces
                        # the active Streamlit configuration.
                        load_uploaded_config(
                            uploaded_config,
                            filename=uploaded_file.name,
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
                    st.json(uploaded_config)

            except json.JSONDecodeError as exc:
                st.error(
                    f"Invalid JSON file: {exc}"
                )

            except UnicodeDecodeError as exc:
                st.error(
                    f"The uploaded file is not valid UTF-8 JSON: {exc}"
                )

            except Exception as exc:
                # This includes semantic errors found while dry-building the
                # RoboAI objects. The existing active configuration remains
                # untouched because state replacement is atomic.
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
            st.json(active_raw_config)

    st.divider()

    # IMPORTANT:
    # Get the configuration again because uploading may have
    # replaced st.session_state.ui_config.
    cfg = st.session_state.ui_config

    # ==========================================================
    # SETUP TABS
    # ==========================================================

    tab_world, tab_materials, tab_sample = st.tabs(
        [
            "World",
            "Materials",
            "Sample",
        ]
    )

    # ==========================================================
    # WORLD
    # ==========================================================

    with tab_world:

        world = cfg["world"]

        with st.form("world_form"):

            c1, c2 = st.columns([1.2, 1])

            with c1:
                material = st.text_input(
                    "World material",
                    value=world["material"],
                    help=(
                        "Use a Geant4 name such as "
                        "G4_AIR or G4_Galactic."
                    ),
                )

            with c2:
                st.caption(
                    "Common choices: G4_AIR, G4_Galactic"
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

            if st.form_submit_button(
                "Save world",
                type="primary",
            ):

                world.update(
                    {
                        "material": material.strip(),
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
    # CUSTOM MATERIALS
    # ==========================================================

    with tab_materials:

        section_title(
            "Custom materials",
            "Use a custom material name anywhere a material "
            "is requested. Composition format: "
            "Cu:0.5,W:0.5",
        )

        rows = records_editor(
            "Custom materials",
            cfg["custom_materials"],
            key="custom_materials_editor",
            column_config={
                "material_name":
                    st.column_config.TextColumn(
                        "Name"
                    ),

                "density_g_cm3":
                    st.column_config.NumberColumn(
                        "Density (g/cm³)",
                        min_value=0.000001,
                    ),

                "composition":
                    st.column_config.TextColumn(
                        "Composition",
                        help=(
                            "Element:fraction pairs "
                            "separated by commas."
                        ),
                    ),
            },
        )

        if st.button(
            "Save materials",
            type="primary",
            key="save_custom_materials",
        ):

            cfg["custom_materials"] = (
                clean_records(
                    rows,
                    "material_name",
                )
            )

            invalidate_simulation()

            st.success(
                "Materials saved."
            )

    # ==========================================================
    # SAMPLE
    # ==========================================================

    with tab_sample:

        sample = cfg["sample"]

        with st.form("sample_form"):

            c1, c2, c3 = st.columns(3)

            name = c1.text_input(
                "Sample name",
                value=sample["name"],
            )

            material = c2.text_input(
                "Material",
                value=sample["material"],
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

            shape = c3.selectbox(
                "Shape",
                shape_options,
                index=shape_options.index(
                    current_shape
                ),
            )

            # ==================================================
            # RECTANGULAR SAMPLE
            # ==================================================

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

            # ==================================================
            # CIRCULAR SAMPLE
            # ==================================================

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

            # ==================================================
            # SAVE SAMPLE
            # ==================================================

            if st.form_submit_button(
                "Save sample",
                type="primary",
            ):

                sample.update(
                    {
                        "name": name.strip(),
                        "material": material.strip(),
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