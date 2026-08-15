import pandas as pd
import streamlit as st


def material_input(
    key_prefix: str,
    object_name: str,
) -> dict:
    material_data = {
        "is_valid": True,
    }

    material_type = st.radio(
        f"Select {object_name} material type",
        options=[
            "Geant4 Material",
            "Custom Material",
        ],
        horizontal=True,
        key=f"{key_prefix}_material_type",
    )

    if material_type == "Geant4 Material":
        material_name = st.text_input(
            f"{object_name} Geant4 material name",
            help="For example: G4_Fe, G4_Cu, G4_Al or G4_Si",
            key=f"{key_prefix}_geant4_material_name",
        ).strip()

        if not material_name:
            st.error("Enter a Geant4 material name.")
            material_data["is_valid"] = False

        material_data.update(
            {
                "material_type": "geant4",
                "material_name": material_name,
            }
        )

        return material_data

    # ---------------------------------------------------------
    # Custom material
    # ---------------------------------------------------------

    custom_material_name = st.text_input(
        f"Custom {object_name} material name",
        key=f"{key_prefix}_custom_material_name",
    ).strip()

    density_g_cm3 = st.number_input(
        "Density (g/cm³)",
        min_value=0.001,
        value=1.0,
        step=0.1,
        key=f"{key_prefix}_density_g_cm3",
    )

    default_composition = pd.DataFrame(
        [
            {
                "Element": "Fe",
                "Mass fraction (%)": 50.0,
            },
            {
                "Element": "Cu",
                "Mass fraction (%)": 50.0,
            },
        ]
    )

    # Permanent composition used by the application.
    composition_data_key = (
        f"{key_prefix}_composition_data"
    )

    # Temporary widget state.
    composition_widget_key = (
        f"_{key_prefix}_composition_editor"
    )

    # Stable input supplied to st.data_editor.
    composition_base_key = (
        f"_{key_prefix}_composition_base"
    )

    if composition_data_key not in st.session_state:
        st.session_state[composition_data_key] = (
            default_composition.copy()
        )

    # Rebuild the stable editor input when the widget is first
    # created or when the user returns to this page.
    if (
        composition_widget_key not in st.session_state
        or composition_base_key not in st.session_state
    ):
        st.session_state[composition_base_key] = (
            st.session_state[composition_data_key]
            .loc[
                :,
                [
                    "Element",
                    "Mass fraction (%)",
                ],
            ]
            .reset_index(drop=True)
            .copy()
        )

    editor_input_df = (
        st.session_state[composition_base_key]
        .reset_index(drop=True)
        .copy()
    )

    # Temporary UI-only column.
    editor_input_df.insert(
        0,
        "Delete",
        False,
    )

    composition_editor_df = st.data_editor(
        editor_input_df,
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key=composition_widget_key,
        column_config={
            "Delete": st.column_config.CheckboxColumn(
                "Delete",
                default=False,
                help="Select rows that you want to remove.",
            ),
            "Element": st.column_config.TextColumn(
                "Element",
                required=True,
                help="Use symbols such as Fe, Cu, Ni or Cr.",
            ),
            "Mass fraction (%)":
                st.column_config.NumberColumn(
                    "Mass fraction (%)",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.000001,
                    format="%.6f",
                    required=True,
                ),
        },
    )

    delete_mask = (
        composition_editor_df["Delete"]
        .fillna(False)
        .astype(bool)
    )

    delete_clicked = st.button(
        "Delete selected rows",
        key=f"_{key_prefix}_delete_composition_rows",
        disabled=not bool(delete_mask.any()),
    )

    if delete_clicked:
        remaining_df = (
            composition_editor_df.loc[
                ~delete_mask,
                [
                    "Element",
                    "Mass fraction (%)",
                ],
            ]
            .reset_index(drop=True)
            .copy()
        )

        # Update both permanent and stable editor data.
        st.session_state[composition_data_key] = (
            remaining_df.copy()
        )

        st.session_state[composition_base_key] = (
            remaining_df.copy()
        )

        # Remove old editor widget state so it reloads
        # using the updated DataFrame.
        st.session_state.pop(
            composition_widget_key,
            None,
        )

        st.rerun()

    # Do not save the temporary Delete column.
    saved_composition_df = (
        composition_editor_df.loc[
            :,
            [
                "Element",
                "Mass fraction (%)",
            ],
        ]
        .reset_index(drop=True)
        .copy()
    )

    # Save current edits permanently.
    st.session_state[composition_data_key] = (
        saved_composition_df.copy()
    )

    composition_df = saved_composition_df.copy()

    composition_df["Mass fraction (%)"] = (
        pd.to_numeric(
            composition_df["Mass fraction (%)"],
            errors="coerce",
        )
    )

    composition_df = composition_df.dropna(
        subset=[
            "Element",
            "Mass fraction (%)",
        ]
    ).copy()

    composition_df["Element"] = (
        composition_df["Element"]
        .astype(str)
        .str.strip()
    )

    composition_df = composition_df[
        composition_df["Element"] != ""
    ].reset_index(drop=True)

    total_percentage = float(
        composition_df[
            "Mass fraction (%)"
        ].sum()
    )

    st.write(
        f"Total mass fraction: "
        f"**{total_percentage:.6f}%**"
    )

    composition_is_valid = (
        not composition_df.empty
        and abs(total_percentage - 100.0) < 0.001
    )

    if not custom_material_name:
        st.error("Enter a custom material name.")
        material_data["is_valid"] = False

    if density_g_cm3 <= 0:
        st.error("Density must be greater than zero.")
        material_data["is_valid"] = False

    if not composition_is_valid:
        st.error(
            "The element mass fractions must add up to 100%."
        )
        material_data["is_valid"] = False
    else:
        st.success("Material composition is valid.")

    composition_list = [
        {
            "element": str(row["Element"]),
            "mass_fraction": (
                float(row["Mass fraction (%)"])
                / 100.0
            ),
        }
        for row in composition_df.to_dict(
            "records"
        )
    ]

    material_data.update(
        {
            "material_type": "custom",
            "material_name": custom_material_name,
            "density_g_cm3": float(density_g_cm3),
            "composition": composition_list,
            "composition_is_valid":
                composition_is_valid,
        }
    )

    return material_data

def geometry_shape_input(
    component_type: str,
    key_prefix: str,
    object_name: str,
) -> dict:
    """
    Display shape-specific Streamlit inputs.

    Supported component types:
        sample
        tube_filter
        detector_filter
        detector_window
        detector
        detector_housing
        collimator

    Returns a JSON-ready dictionary.
    """

    geometry_data = {
        "is_valid": True,
    }

    # Tube filters, detector filters, and detector windows
    # use the same supported shapes.
    filter_like_components = {
        "tube_filter",
        "detector_filter",
        "detector_window",
    }

    if component_type in filter_like_components:
        shape_options = [
            "Rectangular plate",
            "Circular disk",
            "Ring",
        ]

    elif component_type == "sample":
        shape_options = [
            "Rectangular block",
            "Circular cylinder",
            "Sphere",
        ]

    elif component_type == "detector":
        shape_options = [
            "Rectangular detector",
            "Circular detector",
        ]

    elif component_type == "detector_housing":
        # The housing itself is a rectangular box shell.
        # The user chooses only the front aperture shape.
        shape_options = [
            "Circular aperture",
            "Rectangular aperture",
        ]

    elif component_type == "collimator":
        shape_options = [
            "Circular aperture",
            "Rectangular aperture",
        ]

    else:
        raise ValueError(
            f"Unsupported component_type: {component_type}"
        )

    selected_shape = st.selectbox(
        f"Choose {object_name} shape",
        options=shape_options,
        key=f"{key_prefix}_shape",
    )

    geometry_data["shape"] = selected_shape

    # FILTERS AND DETECTOR WINDOWS

    if component_type in filter_like_components:

        if selected_shape == "Rectangular plate":
            width_mm = st.number_input(
                "Width (mm)",
                min_value=0.001,
                step=0.1,
                key=f"{key_prefix}_width_mm",
            )

            height_mm = st.number_input(
                "Height (mm)",
                min_value=0.001,
                step=0.1,
                key=f"{key_prefix}_height_mm",
            )

            thickness_mm = st.number_input(
                "Thickness (mm)",
                min_value=0.001,
                step=0.01,
                key=f"{key_prefix}_thickness_mm",
            )

            geometry_data.update(
                {
                    "geant4_solid": "G4Box",
                    "width_mm": float(width_mm),
                    "height_mm": float(height_mm),
                    "thickness_mm": float(thickness_mm),
                }
            )

        elif selected_shape == "Circular disk":
            radius_mm = st.number_input(
                "Radius (mm)",
                min_value=0.001,
                step=0.1,
                key=f"{key_prefix}_radius_mm",
            )

            thickness_mm = st.number_input(
                "Thickness (mm)",
                min_value=0.001,
                step=0.01,
                key=f"{key_prefix}_thickness_mm",
            )

            geometry_data.update(
                {
                    "geant4_solid": "G4Tubs",
                    "inner_radius_mm": 0.0,
                    "outer_radius_mm": float(radius_mm),
                    "thickness_mm": float(thickness_mm),
                }
            )

        elif selected_shape == "Ring":
            inner_radius_mm = st.number_input(
                "Inner radius (mm)",
                min_value=0.0,
                step=0.1,
                key=f"{key_prefix}_inner_radius_mm",
            )

            outer_radius_mm = st.number_input(
                "Outer radius (mm)",
                min_value=0.001,
                step=0.1,
                key=f"{key_prefix}_outer_radius_mm",
            )

            thickness_mm = st.number_input(
                "Thickness (mm)",
                min_value=0.001,
                step=0.01,
                key=f"{key_prefix}_thickness_mm",
            )

            if inner_radius_mm >= outer_radius_mm:
                st.error(
                    "Inner radius must be smaller than outer radius."
                )
                geometry_data["is_valid"] = False

            geometry_data.update(
                {
                    "geant4_solid": "G4Tubs",
                    "inner_radius_mm": float(inner_radius_mm),
                    "outer_radius_mm": float(outer_radius_mm),
                    "thickness_mm": float(thickness_mm),
                }
            )

    # SAMPLE

    elif component_type == "sample":

        if selected_shape == "Rectangular block":
            width_mm = st.number_input(
                "Sample width (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_width_mm",
            )

            height_mm = st.number_input(
                "Sample height (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_height_mm",
            )

            thickness_mm = st.number_input(
                "Sample thickness (mm)",
                min_value=1e-8,
                step=0.001,
                format="%.4f",
                key=f"{key_prefix}_thickness_mm",
            )

            geometry_data.update(
                {
                    "geant4_solid": "G4Box",
                    "width_mm": float(width_mm),
                    "height_mm": float(height_mm),
                    "thickness_mm": float(thickness_mm),
                }
            )

        elif selected_shape == "Circular cylinder":
            radius_mm = st.number_input(
                "Sample radius (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_radius_mm",
            )

            thickness_mm = st.number_input(
                "Sample thickness (mm)",
                min_value=1e-8,
                step=0.01,
                key=f"{key_prefix}_thickness_mm",
            )

            geometry_data.update(
                {
                    "geant4_solid": "G4Tubs",
                    "inner_radius_mm": 0.0,
                    "outer_radius_mm": float(radius_mm),
                    "thickness_mm": float(thickness_mm),
                }
            )

        elif selected_shape == "Sphere":
            radius_mm = st.number_input(
                "Sample radius (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_radius_mm",
            )

            geometry_data.update(
                {
                    "geant4_solid": "G4Sphere",
                    "radius_mm": float(radius_mm),
                }
            )

    # DETECTOR ACTIVE VOLUME

    elif component_type == "detector":

        if selected_shape == "Rectangular detector":
            width_mm = st.number_input(
                "Active width (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_width_mm",
            )

            height_mm = st.number_input(
                "Active height (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_height_mm",
            )

            thickness_mm = st.number_input(
                "Active thickness (mm)",
                min_value=1e-8,
                step=0.01,
                key=f"{key_prefix}_thickness_mm",
            )

            geometry_data.update(
                {
                    "geant4_solid": "G4Box",
                    "width_mm": float(width_mm),
                    "height_mm": float(height_mm),
                    "thickness_mm": float(thickness_mm),
                }
            )

        elif selected_shape == "Circular detector":
            radius_mm = st.number_input(
                "Active radius (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_radius_mm",
            )

            thickness_mm = st.number_input(
                "Active thickness (mm)",
                min_value=1e-8,
                step=0.01,
                key=f"{key_prefix}_thickness_mm",
            )

            geometry_data.update(
                {
                    "geant4_solid": "G4Tubs",
                    "inner_radius_mm": 0.0,
                    "outer_radius_mm": float(radius_mm),
                    "thickness_mm": float(thickness_mm),
                }
            )


    # DETECTOR HOUSING

    elif component_type == "detector_housing":

        side_gap_mm = st.number_input(
            "Side gap between active detector and cavity wall (mm)",
            min_value=1e-8,
            step=0.1,
            key=f"{key_prefix}_side_gap_mm",
        )

        front_gap_mm = st.number_input(
            "Front gap between window and detector front surface (mm)",
            min_value=1e-8,
            step=0.1,
            key=f"{key_prefix}_front_gap_mm",
        )

        back_gap_mm = st.number_input(
            "Back gap between detector rear surface and cavity wall (mm)",
            min_value=1e-8,
            step=0.1,
            key=f"{key_prefix}_back_gap_mm",
        )

        wall_thickness_mm = st.number_input(
            "Housing wall thickness (mm)",
            min_value=1e-8,
            step=0.1,
            key=f"{key_prefix}_wall_thickness_mm",
        )

        geometry_data.update(
            {
                "geant4_solid": "G4SubtractionSolid",
                "housing_shape": "Rectangular housing",
                "housing_outer_solid": "G4Box",
                "cavity_solid": "G4Box",
                "side_gap_mm": float(side_gap_mm),
                "front_gap_mm": float(front_gap_mm),
                "back_gap_mm": float(back_gap_mm),
                "wall_thickness_mm": float(wall_thickness_mm),
            }
        )

        if selected_shape == "Circular aperture":
            aperture_radius_mm = st.number_input(
                "Housing aperture radius (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_aperture_radius_mm",
            )

            geometry_data.update(
                {
                    "aperture_shape": "circular",
                    "aperture_solid": "G4Tubs",
                    "aperture_radius_mm": float(aperture_radius_mm),
                }
            )

        elif selected_shape == "Rectangular aperture":
            aperture_width_mm = st.number_input(
                "Housing aperture width (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_aperture_width_mm",
            )

            aperture_height_mm = st.number_input(
                "Housing aperture height (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_aperture_height_mm",
            )

            geometry_data.update(
                {
                    "aperture_shape": "rectangular",
                    "aperture_solid": "G4Box",
                    "aperture_width_mm": float(aperture_width_mm),
                    "aperture_height_mm": float(aperture_height_mm),
                }
            )

    # COLLIMATOR

    elif component_type == "collimator":

        if selected_shape == "Circular aperture":
            aperture_radius_mm = st.number_input(
                "Aperture radius (mm)",
                min_value=1e-8,
                step=0.01,
                key=f"{key_prefix}_aperture_radius_mm",
            )

            outer_radius_mm = st.number_input(
                "Outer radius (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_outer_radius_mm",
            )

            length_mm = st.number_input(
                "Collimator length (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_length_mm",
            )

            if aperture_radius_mm >= outer_radius_mm:
                st.error(
                    "Aperture radius must be smaller than outer radius."
                )
                geometry_data["is_valid"] = False

            geometry_data.update(
                {
                    "geant4_solid": "G4Tubs",
                    "aperture_shape": "circular",
                    "aperture_radius_mm":
                        float(aperture_radius_mm),
                    "outer_radius_mm":
                        float(outer_radius_mm),
                    "length_mm": float(length_mm),
                }
            )

        elif selected_shape == "Rectangular aperture":
            outer_width_mm = st.number_input(
                "Outer width (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_outer_width_mm",
            )

            outer_height_mm = st.number_input(
                "Outer height (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_outer_height_mm",
            )

            aperture_width_mm = st.number_input(
                "Aperture width (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_aperture_width_mm",
            )

            aperture_height_mm = st.number_input(
                "Aperture height (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_aperture_height_mm",
            )

            length_mm = st.number_input(
                "Collimator length (mm)",
                min_value=1e-8,
                step=0.1,
                key=f"{key_prefix}_length_mm",
            )

            if aperture_width_mm >= outer_width_mm:
                st.error(
                    "Aperture width must be smaller than outer width."
                )
                geometry_data["is_valid"] = False

            if aperture_height_mm >= outer_height_mm:
                st.error(
                    "Aperture height must be smaller than outer height."
                )
                geometry_data["is_valid"] = False

            geometry_data.update(
                {
                    "geant4_solid": "G4SubtractionSolid",
                    "outer_shape": "G4Box",
                    "aperture_shape": "rectangular",
                    "outer_width_mm": float(outer_width_mm),
                    "outer_height_mm": float(outer_height_mm),
                    "aperture_width_mm":
                        float(aperture_width_mm),
                    "aperture_height_mm":
                        float(aperture_height_mm),
                    "length_mm": float(length_mm),
                }
            )

    return geometry_data




def placement_input(
    key_prefix: str,
    object_name: str,
    default_distance_mm: float = 10.0,
    default_elevation_deg: float = 0.0,
    default_azimuth_deg: float = 0.0,
) -> dict:
    """
    Create reusable position and orientation inputs.

    Position convention:
        - Sample is the reference point.
        - Y is upward.
        - Distance is measured from the sample.

    Orientation modes:
        - face_sample: Geant4 automatically points local +Z at sample.
        - manual: user supplies X/Y/Z rotations.
    """

    placement_data = {
        "is_valid": True,
    }

    # POSITION BLOCK

    st.markdown(f"#### {object_name} position")

    with st.container(
        height=300,
        border=True,
        key=f"{key_prefix}_position_block",
    ):
        distance_from_sample_mm = st.number_input(
            "Distance from sample (mm)",
            min_value=0.001,
            step=1.0,
            key=f"{key_prefix}_distance_from_sample_mm",
        )

        elevation_deg = st.number_input(
            "Position elevation angle (°)",
            min_value=-90.0,
            max_value=90.0,
            step=1.0,
            help="Vertical position angle. Y is the upward axis.",
            key=f"{key_prefix}_position_elevation_deg",
        )

        azimuth_deg = st.number_input(
            "Position azimuth angle (°)",
            min_value=-180.0,
            max_value=180.0,
            step=1.0,
            help="Position angle around the vertical Y axis.",
            key=f"{key_prefix}_position_azimuth_deg",
        )

    # ORIENTATION BLOCK

    st.markdown(f"#### {object_name} orientation")

    with st.container(
        height=330,
        border=True,
        key=f"{key_prefix}_orientation_block",
    ):
        face_sample_key = f"{key_prefix}_face_sample"

        # Set the initial default only on the first visit.
        if face_sample_key not in st.session_state:
            st.session_state[face_sample_key] = True

        face_sample = st.checkbox(
            "Face sample automatically",
            help=(
                "The component's local +Z axis will automatically "
                "point toward the sample."
            ),
            key=face_sample_key,
        )

        if face_sample:
            st.info(
                f"{object_name} will automatically point toward the sample."
            )

            st.caption(
                "Manual rotation is not required. Geant4 will calculate "
                "the orientation from the component position."
            )

            orientation = {
                "mode": "face_sample",
                "rotation_order": "XYZ",
                "rotation_deg": {
                    "x": 0,
                    "y": 0,
                    "z": 0
                },

                
                }

        else:
            st.caption(
                "Manual mode: rotations will be applied around the "
                "Geant4 X, Y and Z axes."
            )

            rotation_x_deg = st.number_input(
                "Rotation X (°)",
                min_value=-180.0,
                max_value=180.0,
                step=1.0,
                key=f"{key_prefix}_rotation_x_deg",
            )

            rotation_y_deg = st.number_input(
                "Rotation Y (°)",
                min_value=-180.0,
                max_value=180.0,
                step=1.0,
                key=f"{key_prefix}_rotation_y_deg",
            )

            rotation_z_deg = st.number_input(
                "Rotation Z (°)",
                min_value=-180.0,
                max_value=180.0,
                step=1.0,
                key=f"{key_prefix}_rotation_z_deg",
            )

            orientation = {
                "mode": "manual",
                "rotation_order": "XYZ",
                "rotation_deg": {
                    "x": float(rotation_x_deg),
                    "y": float(rotation_y_deg),
                    "z": float(rotation_z_deg),
                },
            }
        placement_data["position"] = {
        "reference": "sample",
        "distance_mm": float(distance_from_sample_mm),
        "elevation_deg": float(elevation_deg),
        "azimuth_deg": float(azimuth_deg),
        "vertical_axis": "y",
    }

    placement_data["orientation"] = orientation

    return placement_data