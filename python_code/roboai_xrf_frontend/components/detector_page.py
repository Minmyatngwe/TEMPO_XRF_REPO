from __future__ import annotations

import streamlit as st

from components.common import page_header, records_editor, clean_records
from state import invalidate_simulation


def render_detector_page():
    cfg = st.session_state.ui_config
    detector = cfg["detector"]

    page_header(
        "Detector",
        "Active detector volume, sample-relative placement, housing, masks, filters, and collimators.",
    )

    tabs = st.tabs(
        ["Detector", "Housing", "Internal masks", "Filters", "Collimators"]
    )

    with tabs[0]:

        shape = st.selectbox(
            "Shape",
            ["Circular", "Rectangular"],
            index=["Circular", "Rectangular"].index(detector["shape"]),
            key="detector_shape_selector",
        )

        with st.form("detector_basic_form"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Detector name", value=detector["name"])
            material = c2.text_input("Detector material", value=detector["material"])
            

            if shape == "Circular":
                c1, c2 = st.columns(2)
                radius = c1.number_input(
                    "Radius (mm)",
                    min_value=0.000001,
                    value=float(detector["radius_mm"]),
                )
                thickness = c2.number_input(
                    "Thickness (mm)",
                    min_value=0.000001,
                    value=float(detector["thickness_mm"]),
                )
                width = detector["width_mm"]
                height = detector["height_mm"]
            else:
                c1, c2, c3 = st.columns(3)
                width = c1.number_input(
                    "Width (mm)",
                    min_value=0.000001,
                    value=float(detector["width_mm"]),
                )
                height = c2.number_input(
                    "Height (mm)",
                    min_value=0.000001,
                    value=float(detector["height_mm"]),
                )
                thickness = c3.number_input(
                    "Thickness (mm)",
                    min_value=0.000001,
                    value=float(detector["thickness_mm"]),
                )
                radius = detector["radius_mm"]

            c1, c2, c3 = st.columns(3)
            distance = c1.number_input(
                "Sample → detector (mm)",
                min_value=0.000001,
                value=float(detector["distance_mm"]),
            )
            elevation = c2.number_input(
                "Elevation (deg)", value=float(detector["elevation_deg"])
            )
            azimuth = c3.number_input(
                "Azimuth (deg)", value=float(detector["azimuth_deg"])
            )

            if st.form_submit_button("Save detector", type="primary"):
                detector.update(
                    {
                        "name": name.strip(),
                        "material": material.strip(),
                        "shape": shape,
                        "radius_mm": radius,
                        "width_mm": width,
                        "height_mm": height,
                        "thickness_mm": thickness,
                        "distance_mm": distance,
                        "elevation_deg": elevation,
                        "azimuth_deg": azimuth,
                    }
                )
                invalidate_simulation()
                st.success("Detector saved.")

    with tabs[1]:
        housing = detector["housing"]

        # OUTSIDE the form so changing shape updates the UI immediately
        aperture_shape = st.selectbox(
            "Aperture shape",
            ["Circular", "Rectangular"],
            index=["Circular", "Rectangular"].index(
                housing["aperture_shape"]
            ),
            key="housing_aperture_shape",
        )

        with st.form("housing_form"):

            enabled = st.checkbox(
                "Enable detector housing",
                value=housing["enabled"],
            )

            name = st.text_input(
                "Housing name",
                value=housing["name"],
            )

            # ----------------------------------
            # Aperture geometry
            # ----------------------------------

            if aperture_shape == "Circular":

                aperture_radius = st.number_input(
                    "Aperture radius (mm)",
                    min_value=0.000001,
                    value=float(housing["aperture_radius_mm"]),
                )

                # Keep the old rectangular values
                aperture_width = housing["aperture_width_mm"]
                aperture_height = housing["aperture_height_mm"]

            else:

                c1, c2 = st.columns(2)

                aperture_width = c1.number_input(
                    "Aperture width (mm)",
                    min_value=0.000001,
                    value=float(housing["aperture_width_mm"]),
                )

                aperture_height = c2.number_input(
                    "Aperture height (mm)",
                    min_value=0.000001,
                    value=float(housing["aperture_height_mm"]),
                )

                # Keep the old circular value
                aperture_radius = housing["aperture_radius_mm"]

            # ----------------------------------
            # Housing geometry
            # ----------------------------------

            c1, c2, c3 = st.columns(3)

            clearance = c1.number_input(
                "Detector clearance (mm)",
                min_value=0.0,
                value=float(housing["detector_clearance_mm"]),
            )

            wall = c2.number_input(
                "Housing wall (mm)",
                min_value=0.000001,
                value=float(housing["housing_wall_thickness_mm"]),
            )

            cavity_wall = c3.number_input(
                "Cavity wall (mm)",
                min_value=0.000001,
                value=float(housing["cavity_wall_thickness_mm"]),
            )

            # ----------------------------------
            # Materials
            # ----------------------------------

            c1, c2, c3 = st.columns(3)

            housing_material = c1.text_input(
                "Housing material",
                value=housing["housing_material"],
            )

            cavity_material = c2.text_input(
                "Cavity wall material",
                value=housing["cavity_material"],
            )

            medium = c3.text_input(
                "Inner cavity medium",
                value=housing["inner_cavity_medium_material"],
            )

            c1, c2 = st.columns(2)

            window_material = c1.text_input(
                "Housing window material",
                value=housing["window_material"],
            )

            window_thickness = c2.number_input(
                "Housing window thickness (mm)",
                min_value=0.0000001,
                value=float(housing["window_thickness_mm"]),
                format="%.7f",
            )

            # ----------------------------------
            # Save
            # ----------------------------------

            if st.form_submit_button(
                "Save housing",
                type="primary",
            ):
                housing.update(
                    {
                        "enabled": enabled,
                        "name": name.strip(),
                        "aperture_shape": aperture_shape,
                        "aperture_radius_mm": aperture_radius,
                        "aperture_width_mm": aperture_width,
                        "aperture_height_mm": aperture_height,
                        "detector_clearance_mm": clearance,
                        "housing_wall_thickness_mm": wall,
                        "cavity_wall_thickness_mm": cavity_wall,
                        "housing_material": housing_material.strip(),
                        "cavity_material": cavity_material.strip(),
                        "inner_cavity_medium_material": medium.strip(),
                        "window_material": window_material.strip(),
                        "window_thickness_mm": window_thickness,
                    }
                )

                invalidate_simulation()
                st.success("Housing saved.")

    with tabs[2]:
        st.caption(
            "Masks are aperture geometries in front of the detector and require housing to be enabled."
        )
        circular_masks = [row for row in detector["internal_masks"] if row.get("aperture_shape") == "Circular"]

        rectangular_masks = [row for row in detector["internal_masks"] if row.get("aperture_shape") == "Rectangular"]


        # circular masks 
        st.subheader("Circular masks")
        circular_rows = records_editor(
            "Circular masks",
            circular_masks,
            key="circular_internal_masks_editor",
            column_config=_circular_aperture_columns(),
        )

        # recatangular masks
        st.subheader("Rectangular masks")
        rectangular_rows = records_editor(
            "Rectangular masks",
            rectangular_masks,
            key="rectangular_internal_masks_editor",
            column_config=_rectangular_aperture_columns(),
        )
        
        # save
        if st.button("Save internal masks", type="primary"):
            circular = clean_records(circular_rows, "name")
            rectangular = clean_records(rectangular_rows, "name")

            for row in circular:
                row["aperture_shape"] = "Circular"
            for row in rectangular:
                row["aperture_shape"] = "Rectangular"

            detector["internal_masks"] = circular + rectangular
            invalidate_simulation()
            st.success("Internal masks saved.")

    with tabs[3]:

        circular_filters = [
            row
            for row in detector["filters"]
            if row.get("shape") == "Circular"
        ]

        rectangular_filters = [
            row
            for row in detector["filters"]
            if row.get("shape") == "Rectangular"
        ]

        # ==================================
        # Circular filters
        # ==================================

        st.subheader("Circular filters")

        st.caption(
            "Circular filters use radius and thickness."
        )

        circular_filter_rows = records_editor(
            "Circular filters",
            circular_filters,
            key="circular_detector_filters_editor",
            column_config=_circular_filter_columns(),
        )

        # ==================================
        # Rectangular filters
        # ==================================

        st.subheader("Rectangular filters")

        st.caption(
            "Rectangular filters use width, height, and thickness."
        )

        rectangular_filter_rows = records_editor(
            "Rectangular filters",
            rectangular_filters,
            key="rectangular_detector_filters_editor",
            column_config=_rectangular_filter_columns(),
        )

        # ==================================
        # Save
        # ==================================

        if st.button(
            "Save detector filters",
            type="primary",
        ):

            circular = clean_records(
                circular_filter_rows,
                "name",
            )

            rectangular = clean_records(
                rectangular_filter_rows,
                "name",
            )

            # Add the shape back into the dictionaries
            for row in circular:
                row["shape"] = "Circular"

            for row in rectangular:
                row["shape"] = "Rectangular"

            detector["filters"] = circular + rectangular

            invalidate_simulation()
            st.success("Detector filters saved.")

    with tabs[4]:

        circular_collimators = [
            row
            for row in detector["collimators"]
            if row.get("aperture_shape") == "Circular"
        ]

        rectangular_collimators = [
            row
            for row in detector["collimators"]
            if row.get("aperture_shape") == "Rectangular"
        ]

        # ==================================
        # Circular collimators
        # ==================================

        st.subheader("Circular collimators")

        circular_collimator_rows = records_editor(
            "Circular collimators",
            circular_collimators,
            key="circular_detector_collimators_editor",
            column_config=_circular_collimator_columns(),
        )

        # ==================================
        # Rectangular collimators
        # ==================================

        st.subheader("Rectangular collimators")

        rectangular_collimator_rows = records_editor(
            "Rectangular collimators",
            rectangular_collimators,
            key="rectangular_detector_collimators_editor",
            column_config=_rectangular_collimator_columns(),
        )

        # ==================================
        # Save
        # ==================================

        if st.button(
            "Save detector collimators",
            type="primary",
        ):

            circular = clean_records(
                circular_collimator_rows,
                "name",
            )

            rectangular = clean_records(
                rectangular_collimator_rows,
                "name",
            )

            for row in circular:
                row["aperture_shape"] = "Circular"

            for row in rectangular:
                row["aperture_shape"] = "Rectangular"

            detector["collimators"] = circular + rectangular

            invalidate_simulation()
            st.success("Detector collimators saved.")


def _solid_filter_columns():
    return {
        "enabled": st.column_config.CheckboxColumn("Enabled", default=True),
        "name": st.column_config.TextColumn("Name"),
        "shape": st.column_config.SelectboxColumn(
            "Shape", options=["Circular", "Rectangular"]
        ),
        "material": st.column_config.TextColumn("Material"),
        "radius_mm": st.column_config.NumberColumn("Radius (mm)", min_value=0.0),
        "width_mm": st.column_config.NumberColumn("Width (mm)", min_value=0.0),
        "height_mm": st.column_config.NumberColumn("Height (mm)", min_value=0.0),
        "thickness_mm": st.column_config.NumberColumn("Thickness (mm)", min_value=0.0),
        "distance_mm": st.column_config.NumberColumn("Distance (mm)", min_value=0.0),
    }


def _aperture_columns(include_enabled=False):
    columns = {
        "name": st.column_config.TextColumn("Name"),
        "aperture_shape": st.column_config.SelectboxColumn(
            "Aperture", options=["Circular", "Rectangular"]
        ),
        "material": st.column_config.TextColumn("Material"),
        "aperture_radius_mm": st.column_config.NumberColumn(
            "Aperture radius", min_value=0.0
        ),
        "outer_radius_mm": st.column_config.NumberColumn("Outer radius", min_value=0.0),
        "aperture_width_mm": st.column_config.NumberColumn(
            "Aperture width", min_value=0.0
        ),
        "aperture_height_mm": st.column_config.NumberColumn(
            "Aperture height", min_value=0.0
        ),
        "outer_width_mm": st.column_config.NumberColumn("Outer width", min_value=0.0),
        "outer_height_mm": st.column_config.NumberColumn("Outer height", min_value=0.0),
        "length_mm": st.column_config.NumberColumn("Length (mm)", min_value=0.0),
        "distance_mm": st.column_config.NumberColumn("Distance (mm)", min_value=0.0),
    }
    if include_enabled:
        return {
            "enabled": st.column_config.CheckboxColumn("Enabled", default=True),
            **columns,
        }
    return columns

def _circular_aperture_columns():
    return {
        "name": st.column_config.TextColumn("Name"),
        "material": st.column_config.TextColumn("Material"),
        "aperture_radius_mm": st.column_config.NumberColumn(
            "Aperture radius", min_value=0.0
        ),
        "outer_radius_mm": st.column_config.NumberColumn("Outer radius", min_value=0.0),
        "length_mm": st.column_config.NumberColumn("Length (mm)", min_value=0.0),
        "distance_mm": st.column_config.NumberColumn("Distance (mm)", min_value=0.0),
    }

def _rectangular_aperture_columns():
    return {
        "name": st.column_config.TextColumn("Name"),
        "material": st.column_config.TextColumn("Material"),
        "aperture_width_mm": st.column_config.NumberColumn(
            "Aperture width", min_value=0.0
        ),
        "aperture_height_mm": st.column_config.NumberColumn(
            "Aperture height", min_value=0.0
        ),
        "outer_width_mm": st.column_config.NumberColumn("Outer width", min_value=0.0),
        "outer_height_mm": st.column_config.NumberColumn("Outer height", min_value=0.0),
        "length_mm": st.column_config.NumberColumn("Length (mm)", min_value=0.0),
        "distance_mm": st.column_config.NumberColumn("Distance (mm)", min_value=0.0),
    }

def _circular_filter_columns():
    return {
        "enabled": st.column_config.CheckboxColumn(
            "Enabled",
            default=True,
        ),

        "name": st.column_config.TextColumn(
            "Name"
        ),

        "material": st.column_config.TextColumn(
            "Material"
        ),

        "radius_mm": st.column_config.NumberColumn(
            "Radius (mm)",
            min_value=0.0,
        ),

        "thickness_mm": st.column_config.NumberColumn(
            "Thickness (mm)",
            min_value=0.0,
        ),

        "distance_mm": st.column_config.NumberColumn(
            "Distance (mm)",
            min_value=0.0,
        ),
    }


def _rectangular_filter_columns():
    return {
        "enabled": st.column_config.CheckboxColumn(
            "Enabled",
            default=True,
        ),

        "name": st.column_config.TextColumn(
            "Name"
        ),

        "material": st.column_config.TextColumn(
            "Material"
        ),

        "width_mm": st.column_config.NumberColumn(
            "Width (mm)",
            min_value=0.0,
        ),

        "height_mm": st.column_config.NumberColumn(
            "Height (mm)",
            min_value=0.0,
        ),

        "thickness_mm": st.column_config.NumberColumn(
            "Thickness (mm)",
            min_value=0.0,
        ),

        "distance_mm": st.column_config.NumberColumn(
            "Distance (mm)",
            min_value=0.0,
        ),
    }

def _circular_collimator_columns():
    return {
        "enabled": st.column_config.CheckboxColumn(
            "Enabled",
            default=True,
        ),

        "name": st.column_config.TextColumn(
            "Name"
        ),

        "material": st.column_config.TextColumn(
            "Material"
        ),

        "aperture_radius_mm": st.column_config.NumberColumn(
            "Aperture radius (mm)",
            min_value=0.0,
        ),

        "outer_radius_mm": st.column_config.NumberColumn(
            "Outer radius (mm)",
            min_value=0.0,
        ),

        "length_mm": st.column_config.NumberColumn(
            "Length (mm)",
            min_value=0.0,
        ),

        "distance_mm": st.column_config.NumberColumn(
            "Distance (mm)",
            min_value=0.0,
        ),
    }


def _rectangular_collimator_columns():
    return {
        "enabled": st.column_config.CheckboxColumn(
            "Enabled",
            default=True,
        ),

        "name": st.column_config.TextColumn(
            "Name"
        ),

        "material": st.column_config.TextColumn(
            "Material"
        ),

        "aperture_width_mm": st.column_config.NumberColumn(
            "Aperture width (mm)",
            min_value=0.0,
        ),

        "aperture_height_mm": st.column_config.NumberColumn(
            "Aperture height (mm)",
            min_value=0.0,
        ),

        "outer_width_mm": st.column_config.NumberColumn(
            "Outer width (mm)",
            min_value=0.0,
        ),

        "outer_height_mm": st.column_config.NumberColumn(
            "Outer height (mm)",
            min_value=0.0,
        ),

        "length_mm": st.column_config.NumberColumn(
            "Length (mm)",
            min_value=0.0,
        ),

        "distance_mm": st.column_config.NumberColumn(
            "Distance (mm)",
            min_value=0.0,
        ),
    }