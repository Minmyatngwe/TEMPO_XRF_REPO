from __future__ import annotations

import math

import pandas as pd
import streamlit as st


def page_header(title: str, caption: str):
    st.title(title)
    st.caption(caption)


def section_title(title: str, caption: str | None = None):
    st.subheader(title)
    if caption:
        st.caption(caption)


def records_editor(
    label: str,
    rows: list[dict],
    *,
    key: str,
    column_config=None,
):
    column_config = column_config or {}
    configured_columns = list(column_config.keys())

    if rows:
        frame = pd.DataFrame(rows)

        for column in configured_columns:
            if column not in frame.columns:
                frame[column] = None

        if configured_columns:
            frame = frame[configured_columns]
    else:
        frame = pd.DataFrame(columns=configured_columns)

    edited = st.data_editor(
        frame,
        key=key,
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config=column_config,
    )

    edited = edited.where(pd.notnull(edited), None)
    return edited.to_dict(orient="records")


def clean_records(
    rows: list[dict],
    required_field: str,
) -> list[dict]:
    cleaned = []

    for row in rows:
        value = row.get(required_field)

        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        cleaned.append(row)

    return cleaned


# ==========================================================
# CUSTOM MATERIAL HELPERS
# ==========================================================


def _composition_to_dataframe(
    composition: str,
) -> pd.DataFrame:
    rows = []

    for item in str(composition or "").split(","):
        item = item.strip()

        if not item or ":" not in item:
            continue

        element, fraction = item.split(":", 1)

        try:
            fraction = float(fraction)
        except ValueError:
            fraction = 0.0

        rows.append(
            {
                "element": element.strip(),
                "mass_fraction": fraction,
            }
        )

    if not rows:
        rows = [
            {
                "element": "Fe",
                "mass_fraction": 0.5,
            },
            {
                "element": "Cu",
                "mass_fraction": 0.5,
            },
        ]

    return pd.DataFrame(rows)


def _read_composition_editor(
    edited: pd.DataFrame,
) -> tuple[list[dict], float, bool]:
    rows = []
    rows_valid = True

    for row in edited.to_dict("records"):
        raw_element = row.get("element")

        element = (
            ""
            if raw_element is None
            else str(raw_element).strip()
        )

        fraction = row.get("mass_fraction")

        # Ignore fully empty rows added by st.data_editor.
        if not element and (
            fraction is None
            or pd.isna(fraction)
        ):
            continue

        if not element:
            rows_valid = False
            continue

        try:
            fraction = float(fraction)
        except (TypeError, ValueError):
            rows_valid = False
            continue

        if not 0.0 <= fraction <= 1.0:
            rows_valid = False
            continue

        rows.append(
            {
                "element": element,
                "mass_fraction": fraction,
            }
        )

    total = sum(
        row["mass_fraction"]
        for row in rows
    )

    total_valid = math.isclose(
        total,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    )

    valid = (
        rows_valid
        and bool(rows)
        and total_valid
    )

    return rows, total, valid


def _composition_to_text(
    rows: list[dict],
) -> str:
    return ",".join(
        (
            f"{row['element']}:"
            f"{row['mass_fraction']:.12g}"
        )
        for row in rows
    )


def _render_custom_material_editor(
    *,
    key: str,
    default_name: str = "",
    default_density: float = 1.0,
    default_composition: str = "Fe:0.5,Cu:0.5",
) -> tuple[dict, bool]:
    name = st.text_input(
        "Material name",
        value=default_name,
        key=f"{key}_name",
        placeholder="Example: FeCu",
    ).strip()

    density = st.number_input(
        "Density (g/cm³)",
        min_value=0.000001,
        value=float(default_density),
        format="%.6f",
        key=f"{key}_density",
    )

    st.markdown("**Composition**")

    edited = st.data_editor(
        _composition_to_dataframe(
            default_composition
        ),
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key=f"{key}_composition",
        column_config={
            "element":
                st.column_config.TextColumn(
                    "Element",
                    required=True,
                    help="Example: Fe, Cu, W, Au",
                ),
            "mass_fraction":
                st.column_config.NumberColumn(
                    "Mass fraction",
                    min_value=0.0,
                    max_value=1.0,
                    step=0.01,
                    format="%.6f",
                    required=True,
                    help="Fractions must add up to 1.0.",
                ),
        },
    )

    composition_rows, total, composition_valid = (
        _read_composition_editor(edited)
    )

    if composition_valid:
        st.success(
            f"Total mass fraction: {total:.6f} ✓"
        )
    else:
        st.error(
            "Mass fractions must add up to 1.0. "
            f"Current total: {total:.6f}"
        )

    if not composition_rows:
        st.error("Add at least one element.")

    if not name:
        st.caption("A material name is required.")

    spec = {
        "material_name": name,
        "density_g_cm3": float(density),
        "composition": _composition_to_text(
            composition_rows
        ),
    }

    valid = (
        bool(name)
        and density > 0.0
        and composition_valid
    )

    return spec, valid


def _material_name_exists(
    custom_materials: list[dict],
    name: str,
    *,
    ignore_index: int | None = None,
) -> bool:
    name = name.strip()

    for index, item in enumerate(custom_materials):
        if (
            ignore_index is not None
            and index == ignore_index
        ):
            continue

        if str(
            item.get("material_name", "")
        ).strip() == name:
            return True

    return False


def _invalidate_after_material_change():
    # Local import avoids a module-level dependency on state.py.
    try:
        from state import invalidate_simulation
    except ImportError:
        return

    invalidate_simulation()


def _collect_material_references(
    obj,
    material_name: str,
    path: str = "",
) -> list[str]:
    references = []

    if isinstance(obj, dict):
        for field, value in obj.items():
            # Ignore the registry itself.
            if field == "custom_materials":
                continue

            current_path = (
                f"{path}.{field}"
                if path
                else field
            )

            if (
                isinstance(value, str)
                and value == material_name
                and "material" in field.lower()
            ):
                references.append(current_path)
                continue

            references.extend(
                _collect_material_references(
                    value,
                    material_name,
                    current_path,
                )
            )

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            references.extend(
                _collect_material_references(
                    value,
                    material_name,
                    f"{path}[{index}]",
                )
            )

    return references


def _replace_material_references(
    obj,
    old_name: str,
    new_name: str,
):
    if isinstance(obj, dict):
        for field, value in obj.items():
            if field == "custom_materials":
                continue

            if (
                isinstance(value, str)
                and value == old_name
                and "material" in field.lower()
            ):
                obj[field] = new_name
                continue

            _replace_material_references(
                value,
                old_name,
                new_name,
            )

    elif isinstance(obj, list):
        for value in obj:
            _replace_material_references(
                value,
                old_name,
                new_name,
            )


@st.dialog("New custom material")
def _new_custom_material_dialog(
    custom_materials: list[dict],
    origin_key: str,
):
    st.caption(
        "Create the material once, then reuse it "
        "anywhere a material is requested."
    )

    spec, valid = _render_custom_material_editor(
        key=f"{origin_key}_new_material"
    )

    duplicate = _material_name_exists(
        custom_materials,
        spec["material_name"],
    )

    if duplicate and spec["material_name"]:
        st.error(
            "A custom material with this name "
            "already exists."
        )

    if st.button(
        "Create material",
        type="primary",
        width="stretch",
        key=f"{origin_key}_create_material",
        disabled=not valid or duplicate,
    ):
        save_custom_material(
            custom_materials,
            spec,
        )

        _invalidate_after_material_change()

        # material_input reads this before rebuilding the
        # Custom Material selectbox on the next rerun.
        st.session_state[
            f"{origin_key}_pending_custom_selection"
        ] = spec["material_name"]

        st.toast(
            f"Created {spec['material_name']}.",
            icon="✅",
        )

        st.rerun()


@st.dialog("Manage custom materials")
def _manage_custom_materials_dialog(
    custom_materials: list[dict],
    origin_key: str,
):
    if not custom_materials:
        st.info(
            "No custom materials have been created yet."
        )
        return

    names = [
        str(item.get("material_name", "")).strip()
        for item in custom_materials
        if str(
            item.get("material_name", "")
        ).strip()
    ]

    if not names:
        st.info(
            "No valid custom materials are available."
        )
        return

    selected_name = st.selectbox(
        "Material to edit",
        options=names,
        key=f"{origin_key}_manage_select",
    )

    selected_index = next(
        index
        for index, item in enumerate(custom_materials)
        if str(
            item.get("material_name", "")
        ).strip() == selected_name
    )

    selected = custom_materials[selected_index]

    spec, valid = _render_custom_material_editor(
        key=(
            f"{origin_key}_manage_material_"
            f"{selected_index}"
        ),
        default_name=selected_name,
        default_density=float(
            selected.get("density_g_cm3", 1.0)
        ),
        default_composition=str(
            selected.get(
                "composition",
                "Fe:0.5,Cu:0.5",
            )
        ),
    )

    duplicate = _material_name_exists(
        custom_materials,
        spec["material_name"],
        ignore_index=selected_index,
    )

    if duplicate and spec["material_name"]:
        st.error(
            "Another custom material already uses "
            "this name."
        )

    cfg = st.session_state.get(
        "ui_config",
        {},
    )

    references = _collect_material_references(
        cfg,
        selected_name,
    )

    if references:
        shown = ", ".join(
            references[:5]
        )

        if len(references) > 5:
            shown += " …"

        st.caption(
            f"Currently used by: {shown}"
        )

    save_col, delete_col = st.columns(2)

    if save_col.button(
        "Save changes",
        type="primary",
        width="stretch",
        key=f"{origin_key}_save_managed_material",
        disabled=not valid or duplicate,
    ):
        old_name = selected_name
        new_name = spec["material_name"]

        custom_materials[selected_index] = spec

        # If a material is renamed, update all saved
        # configuration references to the new name.
        if (
            old_name != new_name
            and isinstance(cfg, dict)
        ):
            _replace_material_references(
                cfg,
                old_name,
                new_name,
            )

        _invalidate_after_material_change()

        st.session_state[
            f"{origin_key}_pending_custom_selection"
        ] = new_name

        st.toast(
            f"Saved {new_name}.",
            icon="✅",
        )

        st.rerun()

    if delete_col.button(
        "Delete material",
        width="stretch",
        key=f"{origin_key}_delete_managed_material",
        disabled=bool(references),
    ):
        custom_materials.pop(
            selected_index
        )

        remaining_names = [
            str(
                item.get(
                    "material_name",
                    "",
                )
            ).strip()
            for item in custom_materials
            if str(
                item.get(
                    "material_name",
                    "",
                )
            ).strip()
        ]

        if remaining_names:
            st.session_state[
                f"{origin_key}_pending_custom_selection"
            ] = remaining_names[0]

        _invalidate_after_material_change()

        st.toast(
            f"Deleted {selected_name}.",
            icon="✅",
        )

        st.rerun()

    if references:
        st.warning(
            "This material cannot be deleted while "
            "it is assigned to a configured component."
        )


# ==========================================================
# MATERIAL INPUT
# ==========================================================


def material_input(
    label: str,
    current_material: str,
    custom_materials: list[dict],
    key: str,
    default_geant4: str,
):
    current_material = str(
        current_material or default_geant4
    ).strip()

    existing_custom = next(
        (
            item
            for item in custom_materials
            if str(
                item.get(
                    "material_name",
                    "",
                )
            ).strip() == current_material
        ),
        None,
    )

    current_type = (
        "Custom"
        if existing_custom is not None
        else "Geant4"
    )

    st.markdown(
        f"**{label}**"
    )

    material_type = st.selectbox(
        "Material type",
        [
            "Geant4",
            "Custom",
        ],
        index=(
            1
            if current_type == "Custom"
            else 0
        ),
        key=f"{key}_type",
    )

    # ==========================================================
    # GEANT4 MATERIAL
    # ==========================================================

    if material_type == "Geant4":
        if current_material.startswith("G4_"):
            default_name = current_material
        else:
            default_name = default_geant4

        material_name = st.text_input(
            "Geant4 Material",
            value=default_name,
            key=f"{key}_geant4_name",
            help=(
                "Use a Geant4 material name, for "
                "example G4_Fe, G4_Al, G4_Be."
            ),
        ).strip()

        valid = bool(
            material_name
        )

        if (
            material_name
            and not material_name.startswith("G4_")
        ):
            st.warning(
                "Geant4 material names normally "
                "start with G4_."
            )

        return (
            material_name,
            None,
            valid,
        )

    # ==========================================================
    # CUSTOM MATERIAL
    # ==========================================================

    custom_names = [
        str(item.get("material_name", "")).strip()
        for item in custom_materials
        if str(
            item.get("material_name", "")
        ).strip()
    ]

    select_key = (
        f"{key}_custom_select"
    )

    pending_name = st.session_state.pop(
        f"{key}_pending_custom_selection",
        None,
    )

    # This happens before the selectbox is created, so it is
    # safe to set its session-state value here.
    if pending_name in custom_names:
        st.session_state[
            select_key
        ] = pending_name

    if custom_names:
        if current_material in custom_names:
            default_custom_name = current_material
        else:
            default_custom_name = custom_names[0]

        selected_custom_name = st.selectbox(
            "Custom Material",
            options=custom_names,
            index=custom_names.index(
                default_custom_name
            ),
            key=select_key,
        )

        selected_custom = next(
            item
            for item in custom_materials
            if str(
                item.get(
                    "material_name",
                    "",
                )
            ).strip() == selected_custom_name
        )

        st.caption(
            "Density: "
            f"{float(selected_custom['density_g_cm3']):.6g} "
            "g/cm³"
            "  •  Composition: "
            f"{selected_custom['composition']}"
        )

        valid = True

    else:
        selected_custom_name = ""
        selected_custom = None
        valid = False

        st.info(
            "No custom materials exist yet. "
            "Create one to use a custom material here."
        )

    new_col, manage_col = st.columns(2)

    if new_col.button(
        "+ New custom material",
        width="stretch",
        key=f"{key}_new_custom_button",
    ):
        _new_custom_material_dialog(
            custom_materials,
            key,
        )

    if manage_col.button(
        "Manage materials",
        width="stretch",
        key=f"{key}_manage_custom_button",
        disabled=not bool(
            custom_materials
        ),
    ):
        _manage_custom_materials_dialog(
            custom_materials,
            key,
        )

    return (
        selected_custom_name,
        selected_custom,
        valid,
    )


def save_custom_material(
    custom_materials: list[dict],
    custom_spec: dict | None,
):
    if custom_spec is None:
        return

    name = str(
        custom_spec.get(
            "material_name",
            "",
        )
    ).strip()

    if not name:
        raise ValueError(
            "Custom material name cannot be empty."
        )

    normalized_spec = {
        "material_name": name,
        "density_g_cm3": float(
            custom_spec["density_g_cm3"]
        ),
        "composition": str(
            custom_spec["composition"]
        ).strip(),
    }

    for index, item in enumerate(
        custom_materials
    ):
        if str(
            item.get(
                "material_name",
                "",
            )
        ).strip() == name:
            custom_materials[index] = (
                normalized_spec
            )
            return

    custom_materials.append(
        normalized_spec
    )
