import pandas as pd
import streamlit as st

from helper.frontend_helper import (
    geometry_shape_input,
    material_input,
    placement_input,
)


def components_are_valid(*components: dict) -> bool:
    return all(component.get("is_valid", False) for component in components)


def configured_items_are_valid(enabled: bool, items: list[dict]) -> bool:
    return not enabled or (
        len(items) > 0
        and all(item.get("is_valid", False) for item in items)
    )


def build_spekpy_filters() -> dict:
    st.info(
        "SpekPy applies filter attenuation directly to the generated "
        "X-ray spectrum. These filters will not be constructed in Geant4."
    )

    saved_key = "saved_spekpy_filters"
    default_filters = pd.DataFrame(
        {
            "Material": ["Al"],
            "Thickness (mm)": [0.5],
        }
    )

    if saved_key not in st.session_state:
        st.session_state[saved_key] = default_filters.copy()

    edited_df = st.data_editor(
        st.session_state[saved_key].copy(),
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "Material": st.column_config.TextColumn(
                "Material",
                required=True,
            ),
            "Thickness (mm)": st.column_config.NumberColumn(
                "Thickness (mm)",
                min_value=0.0,
                step=0.01,
                format="%.6f",
                required=True,
            ),
        },
        use_container_width=True,
    )

    st.session_state[saved_key] = edited_df.copy()

    filter_df = edited_df.copy()
    filter_df["Thickness (mm)"] = pd.to_numeric(
        filter_df["Thickness (mm)"],
        errors="coerce",
    )
    filter_df["Material"] = (
        filter_df["Material"].fillna("").astype(str).str.strip()
    )

    empty_rows = (
        (filter_df["Material"] == "")
        & filter_df["Thickness (mm)"].isna()
    )
    filter_df = filter_df[~empty_rows].reset_index(drop=True)

    material_missing = filter_df["Material"] == ""
    thickness_missing = filter_df["Thickness (mm)"].isna()
    thickness_invalid = filter_df["Thickness (mm)"] <= 0

    is_valid = (
        not filter_df.empty
        and not material_missing.any()
        and not thickness_missing.any()
        and not thickness_invalid.any()
    )

    if filter_df.empty:
        st.error("Add at least one SpekPy filter.")
    if material_missing.any():
        st.error("Every SpekPy filter must have a material.")
    if thickness_missing.any():
        st.error("Every SpekPy filter must have a thickness.")
    if thickness_invalid.any():
        st.error("Every filter thickness must be greater than zero.")
    if is_valid:
        st.success("SpekPy filter configuration is valid.")

    filter_list = [
        {
            "name": f"tube_filter_{index + 1}",
            "material": str(row["Material"]),
            "thickness_mm": float(row["Thickness (mm)"]),
            "is_valid": True,
        }
        for index, row in enumerate(filter_df.to_dict("records"))
        if (
            row["Material"]
            and pd.notna(row["Thickness (mm)"])
            and float(row["Thickness (mm)"]) > 0
        )
    ]

    return {
        "filters": filter_list,
        "is_valid": is_valid,
    }


def build_geant4_filters() -> dict:
    number_of_filter = st.number_input(
        "Number of filters",
        min_value=1,
        max_value=10,
        value=1,
        step=1,
        key="number_of_tube_filters",
    )

    filter_list = []

    for filter_index in range(int(number_of_filter)):
        filter_number = filter_index + 1
        object_name = f"Tube Filter {filter_number}"

        with st.expander(object_name):
            geometry = geometry_shape_input(
                component_type="tube_filter",
                key_prefix=f"tube_filter_{filter_number}_geometry",
                object_name=object_name,
            )
            material = material_input(
                key_prefix=f"tube_filter_{filter_number}_material",
                object_name=object_name,
            )
            placement = placement_input(
                key_prefix=f"tube_filter_{filter_number}_placement",
                object_name=object_name,
            )

        filter_list.append(
            {
                "name": f"tube_filter_{filter_number}",
                "geometry": geometry,
                "material": material,
                "placement": placement,
                "is_valid": components_are_valid(
                    geometry,
                    material,
                    placement,
                ),
            }
        )

    return {
        "filters": filter_list,
        "is_valid": all(
            item.get("is_valid", False)
            for item in filter_list
        ),
    }


def build_tube_filter_config() -> tuple[dict, bool, str]:
    use_tube_filter = st.checkbox(
        "Use Tube Filters",
        key="use_tube_filters",
    )

    config = {
        "enabled": use_tube_filter,
        "filter_engine": None,
        "filters": [],
        "is_valid": True,
    }

    internal_medium = "G4_Galactic"

    if use_tube_filter:
        filter_engine = st.selectbox(
            "Filtration method",
            ["SpekPy", "Geant4"],
            key="tube_filter_engine",
        )
        config["filter_engine"] = filter_engine.lower()

        if filter_engine == "SpekPy":
            config.update(build_spekpy_filters())
        else:
            internal_medium = st.text_input(
                "X-ray tube internal medium",
                key="xray_tube_internal_medium",
            )
            config.update(build_geant4_filters())

    tube_filters_valid = configured_items_are_valid(
        use_tube_filter,
        config["filters"],
    )
    config["is_valid"] = tube_filters_valid
    return config, tube_filters_valid, internal_medium


def build_sample_config() -> dict:
    st.subheader("Sample Config")

    with st.container(
        height=400,
        border=True,
        key="sample_shape_parameter_block",
    ):
        sample_geometry = geometry_shape_input(
            component_type="sample",
            key_prefix="sample_geometry",
            object_name="Sample",
        )

    sample_to_tube_air_path_distance = st.number_input(
        "Sample To Tube's Air Path Distance (mm)",
        min_value=0.0,
        step=1.0,
        key="sample_to_tube_air_path_distance_mm",
    )
    source_incident_angle = st.number_input(
        "Source incident azimuth angle (°)",
        min_value=-180.0,
        max_value=180.0,
        step=1.0,
        help="Azimuth position of the X-ray tube around the sample.",
        key="source_incident_azimuth_deg",
    )
    source_elevation_angle = st.number_input(
        "Source elevation angle (°)",
        min_value=-90.0,
        max_value=90.0,
        step=1.0,
        key="source_elevation_deg",
    )
    sample_to_tube_collimator = st.number_input(
        "sample-to-tube-collimator distance (mm)",
        min_value=1e-10,
        step=1.0,
        key="sample_to_tube_collimator_distance_mm",
    )
    tube_collimator_radius = st.number_input(
        "Tube collimator aperture radius (mm)",
        min_value=1e-10,
        step=0.01,
        key="sample_tube_collimator_radius_mm",
    )

    sample_material = material_input(
        key_prefix="sample_material",
        object_name="Sample",
    )

    with st.expander("sample rotation"):
        sample_rotation_x = st.number_input(
            "X Rotation(deg)",
            min_value=0,
            key="sample_rotation_x",
        )
        sample_rotation_y = st.number_input(
            "Y Rotation(deg)",
            min_value=0,
            key="sample_rotation_y",
        )
        sample_rotation_z = st.number_input(
            "Z Rotation (deg)",
            min_value=0,
            key="sample_rotation_z",
        )

    return {
        "geometry": sample_geometry,
        "material": sample_material,
        "sample_to_tube_distance_mm": float(
            sample_to_tube_air_path_distance
        ),
        "source_incident_azimuth_deg": float(source_incident_angle),
        "source_elevation_deg": float(source_elevation_angle),
        "sample_to_tube_collimator_distance_mm": float(
            sample_to_tube_collimator
        ),
        "tube_collimator_radius_mm": float(tube_collimator_radius),
        "sample_rotation_deg": {
            "x": sample_rotation_x,
            "y": sample_rotation_y,
            "z": sample_rotation_z,
        },
        "is_valid": all(
            [
                sample_geometry.get("is_valid", False),
                sample_material.get("is_valid", False),
                sample_to_tube_air_path_distance > 0,
                sample_to_tube_collimator > 0,
                tube_collimator_radius > 0,
            ]
        ),
    }


def build_detector_collimator_config(
    use_detector_housing: bool,
) -> tuple[dict, bool]:
    st.caption(
        "Configure detector collimators and internal masks independently. "
        "Both can be enabled at the same time."
    )

    use_collimator = st.checkbox(
        "Enable detector collimator",
        key="use_detector_collimator",
    )

    use_internal_mask = st.checkbox(
        "Enable internal mask",
        key="use_detector_internal_mask",
        disabled=not use_detector_housing,
        help=(
            "Internal masks are constructed inside the detector housing cavity."
            if use_detector_housing
            else "Enable detector housing first to use an internal mask."
        ),
    )

    config = {
        "enabled": use_collimator or use_internal_mask,
        "collimator": {
            "enabled": use_collimator,
            "components": [],
            "is_valid": True,
        },
        "internal_mask": {
            "enabled": use_internal_mask,
            "components": [],
            "is_valid": True,
        },
        "is_valid": True,
    }

    # -------------------------
    # External detector collimators
    # -------------------------
    if use_collimator:
        number_of_collimators = st.number_input(
            "Number of detector collimators",
            min_value=1,
            value=1,
            step=1,
            key="number_of_detector_collimators",
        )

        for component_index in range(int(number_of_collimators)):
            component_number = component_index + 1
            object_name = f"Collimator {component_number}"
            name = f"detector_collimator_{component_number}"
            key_prefix = f"detector_collimator_{component_number}"

            with st.expander(object_name):
                material = material_input(
                    key_prefix=f"{key_prefix}_material",
                    object_name=object_name,
                )

                with st.container(
                    height=350,
                    border=True,
                    key=f"{key_prefix}_geometry_block",
                ):
                    geometry = geometry_shape_input(
                        component_type="collimator",
                        key_prefix=f"{key_prefix}_geometry",
                        object_name=object_name,
                    )

                placement = placement_input(
                    key_prefix=f"{key_prefix}_placement",
                    object_name=object_name,
                )

            component_valid = components_are_valid(
                geometry,
                material,
                placement,
            )

            config["collimator"]["components"].append(
                {
                    "name": name,
                    "component_type": "collimator",
                    "geometry": geometry,
                    "material": material,
                    "placement": placement,
                    "is_valid": component_valid,
                }
            )

    # -------------------------
    # Internal detector masks
    # -------------------------
    if use_internal_mask:
        st.info(
            "Internal masks are placed inside the detector housing cavity."
        )

        number_of_internal_masks = st.number_input(
            "Number of internal masks",
            min_value=1,
            value=1,
            step=1,
            key="number_of_detector_internal_masks",
        )

        for component_index in range(int(number_of_internal_masks)):
            component_number = component_index + 1
            object_name = f"Internal Mask {component_number}"
            name = f"detector_internal_mask_{component_number}"
            key_prefix = f"detector_internal_mask_{component_number}"

            with st.expander(object_name):
                material = material_input(
                    key_prefix=f"{key_prefix}_material",
                    object_name=object_name,
                )

                with st.container(
                    height=350,
                    border=True,
                    key=f"{key_prefix}_geometry_block",
                ):
                    geometry = geometry_shape_input(
                        component_type="collimator",
                        key_prefix=f"{key_prefix}_geometry",
                        object_name=object_name,
                    )

                distance_from_detector_surface = st.number_input(
                    "Distance from detector surface (mm)",
                    min_value=0.0,
                    step=0.1,
                    key=f"{key_prefix}_distance_from_detector_surface_mm",
                    help=(
                        "Gap measured along the detector cavity local +Z axis, "
                        "starting from the front surface of the active detector."
                    ),
                )

                placement = {
                    "is_valid": True,
                    "position": {
                        "reference": "cavity",
                        "distance_mm": float(
                            distance_from_detector_surface
                        ),
                    },
                }

            component_valid = components_are_valid(
                geometry,
                material,
                placement,
            )

            config["internal_mask"]["components"].append(
                {
                    "name": name,
                    "component_type": "internal_mask",
                    "geometry": geometry,
                    "material": material,
                    "placement": placement,
                    "is_valid": component_valid,
                }
            )

    collimator_valid = configured_items_are_valid(
        use_collimator,
        config["collimator"]["components"],
    )
    internal_mask_valid = configured_items_are_valid(
        use_internal_mask,
        config["internal_mask"]["components"],
    )

    config["collimator"]["is_valid"] = collimator_valid
    config["internal_mask"]["is_valid"] = internal_mask_valid
    config["is_valid"] = collimator_valid and internal_mask_valid

    return config, config["is_valid"]

def build_detector_filter_config() -> tuple[dict, bool]:
    use_detector_filter = st.checkbox(
        "Enable detector filters",
        key="use_detector_filters",
    )

    config = {
        "enabled": use_detector_filter,
        "detector_filters": [],
        "is_valid": True,
    }

    if not use_detector_filter:
        st.caption(
            "No detector-side filter layers will be constructed."
        )
        return config, True

    number_of_detector_filters = st.number_input(
        "Number of filters",
        min_value=1,
        value=1,
        step=1,
        key="number_of_detector_filters",
    )

    for filter_index in range(int(number_of_detector_filters)):
        filter_number = filter_index + 1
        object_name = f"Filter {filter_number}"
        key_prefix = f"detector_filter_{filter_number}"

        with st.expander(object_name):
            material = material_input(
                key_prefix=f"{key_prefix}_material",
                object_name=object_name,
            )

            geometry = geometry_shape_input(
                component_type="detector_filter",
                key_prefix=f"{key_prefix}_geometry",
                object_name=object_name,
            )

            placement = placement_input(
                key_prefix=f"{key_prefix}_placement",
                object_name=object_name,
            )

        config["detector_filters"].append(
            {
                "name": f"detector_filter_{filter_number}",
                "geometry": geometry,
                "material": material,
                "placement": placement,
                "is_valid": components_are_valid(
                    geometry,
                    material,
                    placement,
                ),
            }
        )

    is_valid = configured_items_are_valid(
        use_detector_filter,
        config["detector_filters"],
    )
    config["is_valid"] = is_valid

    return config, is_valid


def build_detector_housing_config() -> dict:
    use_detector_housing = st.checkbox(
        "Enable detector housing",
        key="use_detector_housing",
    )

    config = {
        "enabled": use_detector_housing,
        "is_valid": True,
    }

    if not use_detector_housing:
        return config

    with st.expander("Housing parameters", expanded=True):
        
        cavity_material = st.text_input(
            "Cavity inner material",
            key="detector_housing_cavity_inner_material",
            value="G4_Galactic"
        )
        cavity_wall_thickness_mm=st.number_input(
            "Cavity wall thickness (mm)",
            key="detector_housing_cavity_wall_thickness_mm"
        )
        cavity_wall_material=material_input(
            object_name="Cavity Wall",
            key_prefix="detector_housing_cavity_wall_material"
        )

        material = material_input(
            key_prefix="detector_housing",
            object_name="Detector housing",
        )
        geometry = geometry_shape_input(
            component_type="detector_housing",
            key_prefix="detector_housing_geometry",
            object_name="Detector housing",
        )
        window_material = material_input(
            key_prefix="detector_housing_window",
            object_name="Detector housing Window",
        )
        window_thickness = st.number_input(
            "Detector window thickness (mm)",
            min_value=0.000001,
            step=0.001,
            format="%.4f",
            key="detector_housing_window_thickness_mm",
        )

    cavity_is_valid = bool(cavity_material.strip())
    window_is_valid = all(
        [
            window_material.get("is_valid", False),
            window_thickness > 0,
        ]
    )

    return {
        "enabled": True,
        "geometry": geometry,
        "material": material,
        "cavity": {
            "medium_material": cavity_material.strip(),
            "cavity_wall_thickness_mm":cavity_wall_thickness_mm,
            "material":cavity_wall_material,
            
            "is_valid": cavity_is_valid,
        },
        "window": {
            "material": window_material,
            "thickness_mm": float(window_thickness),
            "is_valid": window_is_valid,
        },
        "is_valid": all(
            [
                geometry.get("is_valid", False),
                material.get("is_valid", False),
                cavity_is_valid,
                window_is_valid,
            ]
        ),
    }



def build_active_detector_config() -> dict:
    st.caption(
        "Configure the detector active volume, material, geometry, and placement."
    )

    material = material_input(
        key_prefix="detector_material",
        object_name="Detector",
    )

    with st.container(
        height=350,
        border=True,
        key="detector_geometry_block",
    ):
        geometry = geometry_shape_input(
            component_type="detector",
            key_prefix="detector_geometry",
            object_name="Detector",
        )

    placement = placement_input(
        key_prefix="detector_placement",
        object_name="Detector",
    )

    return {
        "geometry": geometry,
        "material": material,
        "placement": placement,
        "is_valid": components_are_valid(
            geometry,
            material,
            placement,
        ),
    }


def show_configuration_status(
    xray_tube_ready: bool,
    world_valid: bool,
    tube_filters_valid: bool,
    sample_valid: bool,
    detector_valid: bool,
    detector_collimator_valid: bool,
    detector_filters_valid: bool,
) -> None:
    st.info(
        "Complete and save all X-ray tube and geometry parameters "
        "to enable the Geant4 preview."
    )

    status = {
        "X-ray tube": xray_tube_ready,
        "World material": world_valid,
        "Tube filters": tube_filters_valid,
        "Sample": sample_valid,
        "Detector": detector_valid,
        "Detector aperture": detector_collimator_valid,
        "Detector filters": detector_filters_valid,
    }

    with st.expander("Configuration status", expanded=True):
        for label, valid in status.items():
            if label == "X-ray tube":
                value = "✅ Saved" if valid else "❌ Not saved"
            else:
                value = "✅" if valid else "❌"
            st.write(f"{label}:", value)

st.image(
    "views/images/3d_geometry.png",
    caption="3D geometry",
    width="stretch",
)

world_columns = st.columns(3)
with world_columns[0]:
    word_x_axis_length = st.number_input(
        "World X axis length (mm)",
        min_value=0,
        value=300,
        key="world_x_length_mm",
    )
with world_columns[1]:
    word_y_axis_length = st.number_input(
        "World y axis length (mm)",
        min_value=0,
        value=300,
        key="world_y_length_mm",
    )
with world_columns[2]:
    word_z_axis_length = st.number_input(
        "World z axis length(mm)",
        min_value=0,
        value=300,
        key="world_z_length_mm",
    )

world_mat = st.text_input(
    "World material",
    key="world_material",
).strip()
world_valid = bool(world_mat)

filters, tube_filters_valid, xray_tube_internal_medium = (
    build_tube_filter_config()
)
sample_config = build_sample_config()

st.header("Detector System")

(
    active_detector_tab,
    housing_tab,
    aperture_tab,
    filters_tab,
) = st.tabs(
    [
        "Active Detector",
        "Housing",
        "Aperture",
        "Filters",
    ]
)

with active_detector_tab:
    active_detector_config = build_active_detector_config()

with housing_tab:
    detector_housing_config = build_detector_housing_config()

use_detector_housing = detector_housing_config["enabled"]

with aperture_tab:
    detector_collimator_config, detector_collimator_valid = (
        build_detector_collimator_config(use_detector_housing)
    )

with filters_tab:
    detector_filter_config, detector_filters_valid = (
        build_detector_filter_config()
    )


with st.expander("Detector configuration summary"):
    collimator_count = len(
        detector_collimator_config
        .get("collimator", {})
        .get("components", [])
    )
    internal_mask_count = len(
        detector_collimator_config
        .get("internal_mask", {})
        .get("components", [])
    )
    filter_count = len(
        detector_filter_config.get("detector_filters", [])
    )

    st.write(
        "Active detector:",
        "✅ Complete"
        if active_detector_config.get("is_valid", False)
        else "❌ Incomplete",
    )
    st.write(
        "Housing:",
        (
            "✅ Enabled"
            if detector_housing_config.get("enabled", False)
            else "Disabled"
        ),
    )
    st.write(
        "Detector collimator:",
        (
            f"Enabled ({collimator_count})"
            if detector_collimator_config
            .get("collimator", {})
            .get("enabled", False)
            else "Disabled"
        ),
    )
    st.write(
        "Internal mask:",
        (
            f"Enabled ({internal_mask_count})"
            if detector_collimator_config
            .get("internal_mask", {})
            .get("enabled", False)
            else "Disabled"
        ),
    )
    st.write(
        "Filters:",
        (
            f"Enabled ({filter_count})"
            if detector_filter_config.get("enabled", False)
            else "Disabled"
        ),
    )

world_config = {
    "material": world_mat,
    "world_x_axis_length_mm": word_x_axis_length,
    "world_y_axis_length_mm": word_y_axis_length,
    "world_z_axis_length_mm": word_z_axis_length,
    "is_valid": world_valid,
}

detector_system_config = {
    "active_volume": active_detector_config,
    "housing": detector_housing_config,
    "aperture": detector_collimator_config,
    "detector_layers": detector_filter_config,
    "is_valid": all(
        [
            active_detector_config["is_valid"],
            detector_housing_config["is_valid"],
            detector_collimator_config["is_valid"],
            detector_filter_config["is_valid"],
        ]
    ),
}

full_geometry_config = {
    "world": world_config,
    "tube": {"filters": filters},
    "sample": sample_config,
    "detector": detector_system_config,
}

xray_tube_ready = st.session_state.get("xray_tube_ready", False)
xray_tube_config = dict(
    st.session_state.get("xray_tube_config", {})
)
xray_tube_config["internal_medium"] = (
    xray_tube_internal_medium
)
st.session_state["xray_tube_config"] = xray_tube_config

geometry_inputs_valid = all(
    [
        world_valid,
        tube_filters_valid,
        sample_config["is_valid"],
        active_detector_config["is_valid"],
        detector_housing_config["is_valid"],
        detector_collimator_valid,
        detector_filters_valid,
    ]
)
full_geometry_config["is_valid"] = geometry_inputs_valid
all_inputs_valid = xray_tube_ready and geometry_inputs_valid

if not all_inputs_valid:
    show_configuration_status(
        xray_tube_ready=xray_tube_ready,
        world_valid=world_valid,
        tube_filters_valid=tube_filters_valid,
        sample_valid=sample_config["is_valid"],
        detector_valid=active_detector_config["is_valid"],
        detector_collimator_valid=detector_collimator_valid,
        detector_filters_valid=detector_filters_valid,
    )
else:
    st.success("All required parameters are complete.")

    if st.button(
        "Show complete Json Preview",
        type="primary",
        width="stretch",
        key="complete json preview",
    ):
        st.session_state["geometry_config"] = full_geometry_config

        complete_simulation_config = {
            "xray_tube": xray_tube_config,
            "geometry": full_geometry_config,
            "physics": st.session_state["physics_config"],
        }
        st.session_state[
            "complete_simulation_config"
        ] = complete_simulation_config

        st.success(
            "Configuration is ready for Geant4 geometry generation."
        )

        with st.expander("Complete configuration preview"):
            st.json(complete_simulation_config)
