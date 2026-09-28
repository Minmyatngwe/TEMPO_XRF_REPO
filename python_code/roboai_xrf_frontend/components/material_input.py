from __future__ import annotations

import pandas as pd
import streamlit as st


def normalize_material(value):
    """
    Convert old frontend material values such as:

        "G4_Fe"

    into the new common material structure.
    """

    if isinstance(value, str):
        return {
            "material_type": "geant4",
            "material_name": value,
        }

    if isinstance(value, dict):
        return value

    return {
        "material_type": "geant4",
        "material_name": "G4_AIR",
    }


def material_input(
    label: str,
    value,
    key: str,
):
    material = normalize_material(value)

    current_type = material.get(
        "material_type",
        "geant4",
    )

    st.markdown(f"**{label}**")

    material_type = st.selectbox(
        "Material type",
        options=[
            "Geant4",
            "Custom",
        ],
        index=0 if current_type == "geant4" else 1,
        key=f"{key}_type",
    )

    # Geant4 material

    if material_type == "Geant4":

        default_name = material.get(
            "material_name",
            "G4_AIR",
        )

        if not str(default_name).startswith("G4_"):
            default_name = "G4_AIR"

        material_name = st.text_input(
            "Material",
            value=default_name,
            key=f"{key}_geant4_name",
            help="Example: G4_Fe, G4_Al, G4_AIR, G4_Galactic",
        )

        return {
            "material_type": "geant4",
            "material_name": material_name.strip(),
        }

    # Custom material

    default_name = material.get(
        "material_name",
        "",
    )

    material_name = st.text_input(
        "Material name",
        value=default_name,
        key=f"{key}_custom_name",
    )

    density = st.number_input(
        "Density (g/cm³)",
        min_value=0.000001,
        value=float(
            material.get(
                "density_g_cm3",
                1.0,
            )
        ),
        format="%.6f",
        key=f"{key}_density",
    )

    compositions = material.get(
        "compositions",
        [],
    )

    if not compositions:
        compositions = [
            {
                "element": "Fe",
                "mass_fraction": 1.0,
            }
        ]

    df = pd.DataFrame(compositions)

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        hide_index=True,
        key=f"{key}_composition",
        column_config={
            "element": st.column_config.TextColumn(
                "Element",
                required=True,
            ),
            "mass_fraction": st.column_config.NumberColumn(
                "Mass fraction",
                min_value=0.0,
                max_value=1.0,
                format="%.6f",
                required=True,
            ),
        },
    )

    composition_records = []

    for row in edited.to_dict("records"):

        element = str(
            row.get("element", "")
        ).strip()

        if not element:
            continue

        composition_records.append(
            {
                "element": element,
                "mass_fraction": float(
                    row.get("mass_fraction", 0.0)
                ),
            }
        )

    total = sum(
        row["mass_fraction"]
        for row in composition_records
    )

    if abs(total - 1.0) < 1e-6:
        st.success(
            f"Total mass fraction: {total:.6f}"
        )
    else:
        st.error(
            f"Mass fractions must sum to 1. "
            f"Current total: {total:.6f}"
        )

    return {
        "material_type": "custom",
        "material_name": material_name.strip(),
        "density_g_cm3": density,
        "compositions": composition_records,
    }