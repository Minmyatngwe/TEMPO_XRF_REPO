import json
import hashlib
import copy
import os
import signal
import subprocess

import streamlit as st

from defaults import fresh_default_config


def init_state():
    if "ui_config" not in st.session_state:
        st.session_state.ui_config = fresh_default_config()

    # Compiled RoboAI XRF simulation object
    st.session_state.setdefault(
        "simulation",
        None,
    )

    st.session_state.setdefault(
        "compiled_fingerprint",
        None,
    )

    # ==========================================================
    # GEANT4 PROCESS STATE
    # ==========================================================

    # subprocess.Popen object for the currently running
    # quantitative Geant4 simulation.
    st.session_state.setdefault(
        "geant4_process",
        None,
    )

    st.session_state.setdefault(
        "geant4_running",
        False,
    )

    st.session_state.setdefault(
        "geant4_stopped",
        False,
    )

    st.session_state.setdefault(
        "geant4_beam_on",
        None,
    )

    # ==========================================================
    # RESULTS STATE
    # ==========================================================

    st.session_state.setdefault(
        "run_complete",
        False,
    )

    st.session_state.setdefault(
        "noise_result",
        None,
    )

    st.session_state.setdefault(
        "last_root_file",
        None,
    )

    # ==========================================================
    # IMPORTED CONFIG STATE
    # ==========================================================

    st.session_state.setdefault(
        "loaded_config_name",
        None,
    )

    st.session_state.setdefault(
        "config_was_imported",
        False,
    )

    st.session_state.setdefault(
        "uploaded_config_raw",
        None,
    )


def configuration_fingerprint(
    config: dict,
) -> str:

    payload = {
        key: value
        for key, value in config.items()
        if key not in {
            "run",
            "noise",
        }
    }

    # Run name changes the directory where the configuration
    # and output files are stored.
    payload["run_name"] = config["run"]["run_name"]

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    return hashlib.sha256(
        encoded
    ).hexdigest()


# ==============================================================
# GEANT4 PROCESS HELPERS
# ==============================================================

def stop_geant4_process() -> bool:
    """
    Stop the currently running Geant4 process.

    Returns:
        True  -> a running process was stopped
        False -> there was no active process
    """

    process = st.session_state.get(
        "geant4_process"
    )

    if process is None:
        st.session_state.geant4_running = False
        return False

    # poll() == None means the process is still alive.
    if process.poll() is not None:
        st.session_state.geant4_process = None
        st.session_state.geant4_running = False
        return False

    try:
        # start_run() should create Geant4 with:
        #
        #     start_new_session=True
        #
        # so this terminates the complete process group.
        os.killpg(
            os.getpgid(process.pid),
            signal.SIGTERM,
        )

        try:
            process.wait(
                timeout=5
            )

        except subprocess.TimeoutExpired:
            # If Geant4 refuses to terminate, force it.
            os.killpg(
                os.getpgid(process.pid),
                signal.SIGKILL,
            )

            process.wait()

    except ProcessLookupError:
        # Process already disappeared.
        pass

    except Exception:
        # Fallback in case this process was not launched
        # in its own process group.
        try:
            process.terminate()
            process.wait(timeout=5)

        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    st.session_state.geant4_process = None
    st.session_state.geant4_running = False
    st.session_state.geant4_stopped = True
    st.session_state.run_complete = False
    st.session_state.noise_result = None
    st.session_state.last_root_file = None

    return True


def update_geant4_process_state():
    """
    Check whether the background Geant4 process has finished.

    Returns:
        None -> there is no process
        None return code while running is represented by "running"
        integer -> process exit code
    """

    process = st.session_state.get(
        "geant4_process"
    )

    if process is None:
        st.session_state.geant4_running = False
        return None

    return_code = process.poll()

    if return_code is None:
        st.session_state.geant4_running = True
        return "running"

    # Process finished.
    st.session_state.geant4_running = False
    st.session_state.geant4_process = None

    return return_code


# ==============================================================
# INVALIDATE / RESET
# ==============================================================

def invalidate_simulation():
    """
    Invalidate the compiled simulation.

    If Geant4 is currently running, stop it first so we do not
    leave an orphaned simulation running after configuration
    changes.
    """

    process = st.session_state.get(
        "geant4_process"
    )

    if (
        process is not None
        and process.poll() is None
    ):
        stop_geant4_process()

    st.session_state.simulation = None
    st.session_state.compiled_fingerprint = None

    st.session_state.geant4_process = None
    st.session_state.geant4_running = False
    st.session_state.geant4_stopped = False

    st.session_state.run_complete = False
    st.session_state.noise_result = None
    st.session_state.last_root_file = None


def reset_all():
    """
    Restore the entire frontend to its default state.
    """

    # Stop a running Geant4 process before resetting.
    process = st.session_state.get(
        "geant4_process"
    )

    if (
        process is not None
        and process.poll() is None
    ):
        stop_geant4_process()

    st.session_state.ui_config = (
        fresh_default_config()
    )

    st.session_state.loaded_config_name = None
    st.session_state.config_was_imported = False
    st.session_state.uploaded_config_raw = None

    invalidate_simulation()

# ============================================================
# CONFIG IMPORT HELPERS
# ============================================================

def _material_name(material, default="G4_Galactic"):
    """
    Convert a roboaixrf material object into the simple material
    name used by the frontend.

    Supports:
        "G4_Fe"

    and:

        {
            "material_type": "geant4",
            "material_name": "G4_Fe"
        }
    """

    if material is None:
        return default

    if isinstance(material, str):
        return material

    if isinstance(material, dict):
        return material.get(
            "material_name",
            material.get("name", default),
        )

    return default


def _number(source: dict, key: str, default):
    """
    Safely read a numeric value.
    """
    value = source.get(key)

    if value is None:
        return default

    return value


def _composition_to_string(composition) -> str:
    """
    Convert a custom-material composition into the frontend
    Cu:0.5,W:0.5 representation where possible.
    """

    if composition is None:
        return ""

    if isinstance(composition, str):
        return composition

    if isinstance(composition, dict):
        return ",".join(
            f"{element}:{fraction}"
            for element, fraction in composition.items()
        )

    if isinstance(composition, list):
        parts = []

        for item in composition:
            if isinstance(item, dict):
                element = (
                    item.get("element")
                    or item.get("symbol")
                    or item.get("name")
                )

                fraction = (
                    item.get("fraction")
                    or item.get("mass_fraction")
                    or item.get("value")
                )

                if element is not None and fraction is not None:
                    parts.append(f"{element}:{fraction}")

        return ",".join(parts)

    return str(composition)


def _collect_custom_materials(config: dict) -> list[dict]:
    """
    Find custom material definitions anywhere in the uploaded config.
    """

    found = {}


    def walk(value):
        if isinstance(value, dict):

            material_type = str(
                value.get("material_type", "")
            ).lower()

            if material_type == "custom":
                name = value.get("material_name")

                if name:
                    found[name] = {
                        "material_name": name,
                        "density_g_cm3": float(
                            value.get(
                                "density_g_cm3",
                                value.get("density", 1.0),
                            )
                        ),
                        "composition": _composition_to_string(
                            value.get("composition")
                        ),
                    }

            for child in value.values():
                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)


    walk(config)

    return list(found.values())


# ============================================================
# STRICT ROBOAIXRF CONFIG VALIDATION / IMPORT HELPERS
# ============================================================


class RoboAIConfigValidationError(ValueError):
    """Raised when an uploaded file is not a valid RoboAI config.json."""


def _validation_error(errors: list[str]) -> None:
    if not errors:
        return

    details = "\n".join(f"- {message}" for message in errors)
    raise RoboAIConfigValidationError(
        "Invalid RoboAI XRF configuration. The file was not loaded.\n"
        f"{details}"
    )


def _require_dict(value, path: str, errors: list[str]):
    if not isinstance(value, dict):
        errors.append(f"{path} must be a JSON object.")
        return None
    return value


def _require_list(value, path: str, errors: list[str]):
    if not isinstance(value, list):
        errors.append(f"{path} must be a JSON array.")
        return None
    return value


def _require_key(obj: dict, key: str, path: str, errors: list[str]):
    if key not in obj:
        errors.append(f"Missing required key: {path}.{key}")
        return None
    return obj[key]


def _require_number(obj: dict, key: str, path: str, errors: list[str]):
    value = _require_key(obj, key, path, errors)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{path}.{key} must be a JSON number.")
        return None
    return value


def _require_string(obj: dict, key: str, path: str, errors: list[str]):
    value = _require_key(obj, key, path, errors)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}.{key} must be a non-empty string.")
        return None
    return value


def _validate_material(material, path: str, errors: list[str]) -> None:
    material = _require_dict(material, path, errors)
    if material is None:
        return

    material_type = _require_string(
        material,
        "material_type",
        path,
        errors,
    )
    _require_string(
        material,
        "material_name",
        path,
        errors,
    )

    if material_type is not None and material_type.lower() == "custom":
        _require_number(
            material,
            "density_g_cm3",
            path,
            errors,
        )

        composition = _require_key(
            material,
            "composition",
            path,
            errors,
        )

        if composition is not None and not isinstance(
            composition,
            (list, dict),
        ):
            errors.append(
                f"{path}.composition must be a JSON array or object."
            )


def _validate_solid_geometry(geometry, path: str, errors: list[str]) -> None:
    geometry = _require_dict(geometry, path, errors)
    if geometry is None:
        return

    shape = _require_string(
        geometry,
        "shape",
        path,
        errors,
    )

    _require_number(
        geometry,
        "thickness_mm",
        path,
        errors,
    )

    if shape == "Circular":
        _require_number(
            geometry,
            "radius_mm",
            path,
            errors,
        )

    elif shape == "Rectangular":
        _require_number(
            geometry,
            "width_mm",
            path,
            errors,
        )
        _require_number(
            geometry,
            "height_mm",
            path,
            errors,
        )

    elif shape is not None:
        errors.append(
            f"{path}.shape must be 'Circular' or 'Rectangular'; got {shape!r}."
        )


def _validate_aperture_geometry(geometry, path: str, errors: list[str]) -> None:
    geometry = _require_dict(geometry, path, errors)
    if geometry is None:
        return

    shape = _require_string(
        geometry,
        "aperture_shape",
        path,
        errors,
    )

    _require_number(
        geometry,
        "length_mm",
        path,
        errors,
    )

    if shape == "Circular":
        _require_number(
            geometry,
            "aperture_radius_mm",
            path,
            errors,
        )
        _require_number(
            geometry,
            "outer_radius_mm",
            path,
            errors,
        )

    elif shape == "Rectangular":
        _require_number(
            geometry,
            "aperture_width_mm",
            path,
            errors,
        )
        _require_number(
            geometry,
            "aperture_height_mm",
            path,
            errors,
        )
        _require_number(
            geometry,
            "outer_width_mm",
            path,
            errors,
        )
        _require_number(
            geometry,
            "outer_height_mm",
            path,
            errors,
        )

    elif shape is not None:
        errors.append(
            f"{path}.aperture_shape must be 'Circular' or 'Rectangular'; "
            f"got {shape!r}."
        )


def _validate_position_placement(
    placement,
    path: str,
    errors: list[str],
    *,
    require_angles: bool,
) -> None:
    placement = _require_dict(placement, path, errors)
    if placement is None:
        return

    # RoboAI Placement serializes its position inside "position".  Keeping
    # the direct form accepted here also supports package versions where the
    # position fields are serialized directly on the placement object.
    position = placement.get("position", placement)
    position_path = f"{path}.position" if "position" in placement else path

    position = _require_dict(
        position,
        position_path,
        errors,
    )
    if position is None:
        return

    _require_number(
        position,
        "distance_mm",
        position_path,
        errors,
    )

    if require_angles:
        _require_number(
            position,
            "elevation_deg",
            position_path,
            errors,
        )
        _require_number(
            position,
            "azimuth_deg",
            position_path,
            errors,
        )


def _validate_solid_component(component, path: str, errors: list[str]) -> None:
    component = _require_dict(component, path, errors)
    if component is None:
        return

    _require_string(component, "name", path, errors)

    geometry = _require_key(
        component,
        "geometry",
        path,
        errors,
    )
    if geometry is not None:
        _validate_solid_geometry(
            geometry,
            f"{path}.geometry",
            errors,
        )

    material = _require_key(
        component,
        "material",
        path,
        errors,
    )
    if material is not None:
        _validate_material(
            material,
            f"{path}.material",
            errors,
        )

    placement = _require_key(
        component,
        "placement",
        path,
        errors,
    )
    if placement is not None:
        _validate_position_placement(
            placement,
            f"{path}.placement",
            errors,
            require_angles=False,
        )


def _validate_aperture_component(component, path: str, errors: list[str]) -> None:
    component = _require_dict(component, path, errors)
    if component is None:
        return

    _require_string(component, "name", path, errors)

    geometry = _require_key(
        component,
        "geometry",
        path,
        errors,
    )
    if geometry is not None:
        _validate_aperture_geometry(
            geometry,
            f"{path}.geometry",
            errors,
        )

    material = _require_key(
        component,
        "material",
        path,
        errors,
    )
    if material is not None:
        _validate_material(
            material,
            f"{path}.material",
            errors,
        )

    placement = _require_key(
        component,
        "placement",
        path,
        errors,
    )
    if placement is not None:
        _validate_position_placement(
            placement,
            f"{path}.placement",
            errors,
            require_angles=False,
        )


def _validate_tube_placement(
    tube: dict,
    path: str,
    errors: list[str],
) -> None:
    placement = _require_key(
        tube,
        "placement",
        path,
        errors,
    )
    placement = _require_dict(
        placement,
        f"{path}.placement",
        errors,
    )
    if placement is None:
        return

    # Current TubePlacement serialization.
    if "focal_spot_to_sample_distance_mm" in placement:
        _require_number(
            placement,
            "focal_spot_to_sample_distance_mm",
            f"{path}.placement",
            errors,
        )
        _require_number(
            placement,
            "tube_window_to_sample_distance_mm",
            f"{path}.placement",
            errors,
        )
        _require_number(
            placement,
            "elevation_deg",
            f"{path}.placement",
            errors,
        )
        _require_number(
            placement,
            "azimuth_deg",
            f"{path}.placement",
            errors,
        )
        return

    # Older RoboAI serialization using Placement.position.
    position = placement.get("position")
    if position is None:
        errors.append(
            f"{path}.placement must contain either "
            "focal_spot_to_sample_distance_mm or position."
        )
        return

    _validate_position_placement(
        placement,
        f"{path}.placement",
        errors,
        require_angles=True,
    )

    _require_number(
        tube,
        "tube_window_to_sample_distance_mm",
        path,
        errors,
    )


def _validate_housing(housing, path: str, errors: list[str]) -> None:
    housing = _require_dict(housing, path, errors)
    if housing is None:
        return

    _require_string(housing, "name", path, errors)

    geometry = _require_key(
        housing,
        "geometry",
        path,
        errors,
    )
    geometry = _require_dict(
        geometry,
        f"{path}.geometry",
        errors,
    )

    if geometry is not None:
        aperture_shape = _require_string(
            geometry,
            "aperture_shape",
            f"{path}.geometry",
            errors,
        )

        _require_number(
            geometry,
            "detector_clearance_mm",
            f"{path}.geometry",
            errors,
        )
        _require_number(
            geometry,
            "housing_wall_thickness_mm",
            f"{path}.geometry",
            errors,
        )
        _require_number(
            geometry,
            "cavity_wall_thickness_mm",
            f"{path}.geometry",
            errors,
        )

        if aperture_shape == "Circular":
            _require_number(
                geometry,
                "aperture_radius_mm",
                f"{path}.geometry",
                errors,
            )
        elif aperture_shape == "Rectangular":
            _require_number(
                geometry,
                "aperture_width_mm",
                f"{path}.geometry",
                errors,
            )
            _require_number(
                geometry,
                "aperture_height_mm",
                f"{path}.geometry",
                errors,
            )
        elif aperture_shape is not None:
            errors.append(
                f"{path}.geometry.aperture_shape must be 'Circular' or "
                f"'Rectangular'; got {aperture_shape!r}."
            )

    for material_key in (
        "housing_material",
        "cavity_wall_material",
        "inner_cavity_medium_material",
        "window_material",
    ):
        material = _require_key(
            housing,
            material_key,
            path,
            errors,
        )
        if material is not None:
            _validate_material(
                material,
                f"{path}.{material_key}",
                errors,
            )

    _require_number(
        housing,
        "window_thickness_mm",
        path,
        errors,
    )


def validate_roboaixrf_config(source: dict) -> None:
    """
    Validate an uploaded exported RoboAI config.json before changing state.

    The importer deliberately does not accept the Streamlit ui_config format.
    Required RoboAI keys must be present under their canonical names; missing
    or misspelled keys are rejected instead of being replaced by defaults.
    """

    errors: list[str] = []

    source = _require_dict(source, "root", errors)
    if source is None:
        _validation_error(errors)
        return

    # Prevent accidentally loading the frontend's internal format.
    frontend_only_keys = {
        "tube",
        "run",
        "noise",
        "custom_materials",
    }
    found_frontend_keys = sorted(frontend_only_keys.intersection(source))
    if found_frontend_keys:
        errors.append(
            "This is a Streamlit frontend configuration, not an exported "
            "RoboAI config.json. Frontend-only key(s): "
            + ", ".join(found_frontend_keys)
        )

    required_top_level = {
        "world",
        "xray_tube",
        "sample",
        "detector",
        "physics",
    }

    for key in sorted(required_top_level):
        if key not in source:
            errors.append(f"Missing required top-level key: {key}")

    # Reject clearly foreign top-level formats while allowing the known
    # RoboAI references_names metadata field.
    allowed_top_level = required_top_level | {"references_names"}
    unexpected_top_level = sorted(set(source) - allowed_top_level)
    for key in unexpected_top_level:
        errors.append(f"Unexpected top-level key: {key}")

    # --------------------------------------------------------
    # WORLD
    # --------------------------------------------------------
    world = source.get("world")
    world = _require_dict(world, "world", errors)
    if world is not None:
        material = _require_key(
            world,
            "world_material",
            "world",
            errors,
        )
        if material is not None:
            _validate_material(
                material,
                "world.world_material",
                errors,
            )

        for key in (
            "world_size_x_mm",
            "world_size_y_mm",
            "world_size_z_mm",
        ):
            _require_number(
                world,
                key,
                "world",
                errors,
            )

    # --------------------------------------------------------
    # SAMPLE
    # --------------------------------------------------------
    sample = source.get("sample")
    sample = _require_dict(sample, "sample", errors)
    if sample is not None:
        _require_string(sample, "name", "sample", errors)

        geometry = _require_key(
            sample,
            "geometry",
            "sample",
            errors,
        )
        if geometry is not None:
            _validate_solid_geometry(
                geometry,
                "sample.geometry",
                errors,
            )

        material = _require_key(
            sample,
            "material",
            "sample",
            errors,
        )
        if material is not None:
            _validate_material(
                material,
                "sample.material",
                errors,
            )

    # --------------------------------------------------------
    # X-RAY TUBE
    # --------------------------------------------------------
    tube = source.get("xray_tube")
    tube = _require_dict(tube, "xray_tube", errors)
    if tube is not None:
        for key in (
            "name",
            "anode_symbol",
            "tube_type",
        ):
            _require_string(
                tube,
                key,
                "xray_tube",
                errors,
            )

        for key in (
            "current_ma",
            "voltage_kv",
            "anode_angle_deg",
            "focal_spot_diameter_mm",
            "tube_collimator_radius_mm",
            "tube_window_to_virtual_collimator_distance_mm",
            "target_thickness_um",
        ):
            _require_number(
                tube,
                key,
                "xray_tube",
                errors,
            )

        _validate_tube_placement(
            tube,
            "xray_tube",
            errors,
        )

        tube_window = _require_key(
            tube,
            "tube_window",
            "xray_tube",
            errors,
        )
        tube_window = _require_dict(
            tube_window,
            "xray_tube.tube_window",
            errors,
        )
        if tube_window is not None:
            _require_string(
                tube_window,
                "name",
                "xray_tube.tube_window",
                errors,
            )
            _require_number(
                tube_window,
                "thickness_mm",
                "xray_tube.tube_window",
                errors,
            )
            material = _require_key(
                tube_window,
                "material",
                "xray_tube.tube_window",
                errors,
            )
            if material is not None:
                _validate_material(
                    material,
                    "xray_tube.tube_window.material",
                    errors,
                )

        spekpy_filters = _require_key(
            tube,
            "tube_filter_spekpy",
            "xray_tube",
            errors,
        )
        spekpy_filters = _require_list(
            spekpy_filters,
            "xray_tube.tube_filter_spekpy",
            errors,
        )
        if spekpy_filters is not None:
            for index, item in enumerate(spekpy_filters):
                item_path = f"xray_tube.tube_filter_spekpy[{index}]"
                item = _require_dict(item, item_path, errors)
                if item is None:
                    continue
                _require_string(item, "element", item_path, errors)
                _require_number(item, "thickness_mm", item_path, errors)

        geant4_filters = _require_key(
            tube,
            "tube_filters_geant4",
            "xray_tube",
            errors,
        )
        geant4_filters = _require_list(
            geant4_filters,
            "xray_tube.tube_filters_geant4",
            errors,
        )
        if geant4_filters is not None:
            for index, item in enumerate(geant4_filters):
                _validate_solid_component(
                    item,
                    f"xray_tube.tube_filters_geant4[{index}]",
                    errors,
                )

    # --------------------------------------------------------
    # DETECTOR
    # --------------------------------------------------------
    detector = source.get("detector")
    detector = _require_dict(detector, "detector", errors)
    if detector is not None:
        _require_string(detector, "name", "detector", errors)

        geometry = _require_key(
            detector,
            "geometry",
            "detector",
            errors,
        )
        if geometry is not None:
            _validate_solid_geometry(
                geometry,
                "detector.geometry",
                errors,
            )

        material = _require_key(
            detector,
            "material",
            "detector",
            errors,
        )
        if material is not None:
            _validate_material(
                material,
                "detector.material",
                errors,
            )

        placement = _require_key(
            detector,
            "placement",
            "detector",
            errors,
        )
        if placement is not None:
            _validate_position_placement(
                placement,
                "detector.placement",
                errors,
                require_angles=True,
            )

        detector_filters = _require_key(
            detector,
            "detector_filters",
            "detector",
            errors,
        )
        detector_filters = _require_list(
            detector_filters,
            "detector.detector_filters",
            errors,
        )
        if detector_filters is not None:
            for index, item in enumerate(detector_filters):
                _validate_solid_component(
                    item,
                    f"detector.detector_filters[{index}]",
                    errors,
                )

        detector_collimators = _require_key(
            detector,
            "detector_collimators",
            "detector",
            errors,
        )
        detector_collimators = _require_list(
            detector_collimators,
            "detector.detector_collimators",
            errors,
        )
        if detector_collimators is not None:
            for index, item in enumerate(detector_collimators):
                _validate_aperture_component(
                    item,
                    f"detector.detector_collimators[{index}]",
                    errors,
                )

        internal_masks = _require_key(
            detector,
            "internal_masks",
            "detector",
            errors,
        )
        internal_masks = _require_list(
            internal_masks,
            "detector.internal_masks",
            errors,
        )
        if internal_masks is not None:
            for index, item in enumerate(internal_masks):
                _validate_aperture_component(
                    item,
                    f"detector.internal_masks[{index}]",
                    errors,
                )

        if "housing" in detector and detector["housing"] is not None:
            _validate_housing(
                detector["housing"],
                "detector.housing",
                errors,
            )

    # --------------------------------------------------------
    # PHYSICS
    # --------------------------------------------------------
    physics = source.get("physics")
    physics = _require_dict(physics, "physics", errors)
    if physics is not None:
        required_physics = fresh_default_config()["physics"]

        for key, default_value in required_physics.items():
            value = _require_key(
                physics,
                key,
                "physics",
                errors,
            )
            if value is None:
                continue

            if isinstance(default_value, bool):
                if not isinstance(value, bool):
                    errors.append(f"physics.{key} must be true or false.")
            elif isinstance(default_value, int):
                if isinstance(value, bool) or not isinstance(value, int):
                    errors.append(f"physics.{key} must be an integer.")
            elif isinstance(default_value, float):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    errors.append(f"physics.{key} must be a JSON number.")
            elif isinstance(default_value, str):
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"physics.{key} must be a non-empty string.")

    _validation_error(errors)


def _placement_position(placement: dict) -> dict:
    """Return the position payload from a RoboAI Placement export."""
    return placement.get("position", placement)


def _import_solid_component(component: dict) -> dict:
    geometry = component["geometry"]
    position = _placement_position(component["placement"])

    return {
        "enabled": bool(component.get("enabled", True)),
        "name": str(component["name"]),
        "shape": geometry["shape"],
        "material": _material_name(component["material"]),
        "radius_mm": float(geometry.get("radius_mm") or 0.0),
        "width_mm": float(geometry.get("width_mm") or 0.0),
        "height_mm": float(geometry.get("height_mm") or 0.0),
        "thickness_mm": float(geometry["thickness_mm"]),
        "distance_mm": float(position["distance_mm"]),
    }


def _import_aperture_component(component: dict) -> dict:
    geometry = component["geometry"]
    position = _placement_position(component["placement"])

    return {
        "enabled": bool(component.get("enabled", True)),
        "name": str(component["name"]),
        "aperture_shape": geometry["aperture_shape"],
        "material": _material_name(component["material"]),
        "aperture_radius_mm": float(
            geometry.get("aperture_radius_mm") or 0.0
        ),
        "outer_radius_mm": float(
            geometry.get("outer_radius_mm") or 0.0
        ),
        "aperture_width_mm": float(
            geometry.get("aperture_width_mm") or 0.0
        ),
        "aperture_height_mm": float(
            geometry.get("aperture_height_mm") or 0.0
        ),
        "outer_width_mm": float(
            geometry.get("outer_width_mm") or 0.0
        ),
        "outer_height_mm": float(
            geometry.get("outer_height_mm") or 0.0
        ),
        "length_mm": float(geometry["length_mm"]),
        "distance_mm": float(position["distance_mm"]),
    }



# ============================================================
# MAIN ROBOAIXRF -> UI CONVERTER
# ============================================================

def import_roboaixrf_config(source: dict) -> dict:
    """
    Convert a *validated* exported RoboAI config.json into the simplified
    configuration used by the Streamlit frontend.

    Important: validation happens before this conversion.  Required values
    are read directly from the uploaded file and are never silently replaced
    with DEFAULT_CONFIG values.  Defaults remain only for frontend-only
    settings (run/noise) and dimensions that are irrelevant to the selected
    geometry shape.
    """

    validate_roboaixrf_config(source)

    cfg = fresh_default_config()

    # ========================================================
    # WORLD
    # ========================================================

    world_src = source["world"]

    cfg["world"] = {
        "material": _material_name(world_src["world_material"]),
        "size_x_mm": float(world_src["world_size_x_mm"]),
        "size_y_mm": float(world_src["world_size_y_mm"]),
        "size_z_mm": float(world_src["world_size_z_mm"]),
    }

    # ========================================================
    # CUSTOM MATERIALS
    # ========================================================

    # Always replace the frontend list.  If the uploaded RoboAI file uses no
    # custom materials, this must become [] rather than keeping the example
    # CuWCollimator from DEFAULT_CONFIG.
    cfg["custom_materials"] = _collect_custom_materials(source)

    # ========================================================
    # SAMPLE
    # ========================================================

    sample_src = source["sample"]
    sample_geometry = sample_src["geometry"]
    sample = cfg["sample"]

    sample["name"] = str(sample_src["name"])
    sample["material"] = _material_name(sample_src["material"])
    sample["shape"] = sample_geometry["shape"]
    sample["thickness_mm"] = float(sample_geometry["thickness_mm"])

    if sample["shape"] == "Circular":
        sample["radius_mm"] = float(sample_geometry["radius_mm"])
    else:
        sample["width_mm"] = float(sample_geometry["width_mm"])
        sample["height_mm"] = float(sample_geometry["height_mm"])

    # ========================================================
    # X-RAY TUBE
    # ========================================================

    tube_src = source["xray_tube"]
    tube = cfg["tube"]

    tube["name"] = str(tube_src["name"])
    tube["current_ma"] = float(tube_src["current_ma"])
    tube["voltage_kv"] = float(tube_src["voltage_kv"])
    tube["anode_angle_deg"] = float(tube_src["anode_angle_deg"])
    tube["anode_symbol"] = str(tube_src["anode_symbol"])
    tube["focal_spot_diameter_mm"] = float(
        tube_src["focal_spot_diameter_mm"]
    )
    tube["tube_collimator_radius_mm"] = float(
        tube_src["tube_collimator_radius_mm"]
    )
    tube["tube_window_to_virtual_collimator_distance_mm"] = float(
        tube_src["tube_window_to_virtual_collimator_distance_mm"]
    )
    tube["tube_type"] = str(tube_src["tube_type"])
    tube["target_thickness_um"] = float(tube_src["target_thickness_um"])

    # TubePlacement has existed in two serialized layouts.  Neither branch
    # uses defaults: whichever format is present must contain every required
    # field and has already passed strict validation above.
    tube_placement = tube_src["placement"]

    if "focal_spot_to_sample_distance_mm" in tube_placement:
        tube["focal_spot_to_sample_distance_mm"] = float(
            tube_placement["focal_spot_to_sample_distance_mm"]
        )
        tube["tube_window_to_sample_distance_mm"] = float(
            tube_placement["tube_window_to_sample_distance_mm"]
        )
        tube["elevation_deg"] = float(tube_placement["elevation_deg"])
        tube["azimuth_deg"] = float(tube_placement["azimuth_deg"])
    else:
        tube_position = tube_placement["position"]
        tube["focal_spot_to_sample_distance_mm"] = float(
            tube_position["distance_mm"]
        )
        tube["tube_window_to_sample_distance_mm"] = float(
            tube_src["tube_window_to_sample_distance_mm"]
        )
        tube["elevation_deg"] = float(tube_position["elevation_deg"])
        tube["azimuth_deg"] = float(tube_position["azimuth_deg"])

    window_src = tube_src["tube_window"]
    tube["window"] = {
        "name": str(window_src["name"]),
        "material": _material_name(window_src["material"]),
        "thickness_mm": float(window_src["thickness_mm"]),
    }

    tube["spekpy_filters"] = [
        {
            "element": str(item["element"]),
            "thickness_mm": float(item["thickness_mm"]),
        }
        for item in tube_src["tube_filter_spekpy"]
    ]

    # Exported RoboAI Filter objects are nested.  Convert them into the flat
    # table rows used by the Streamlit editor/builder.
    tube["geant4_filters"] = [
        _import_solid_component(item)
        for item in tube_src["tube_filters_geant4"]
    ]

    # ========================================================
    # DETECTOR
    # ========================================================

    detector_src = source["detector"]
    detector_geometry = detector_src["geometry"]
    detector_position = _placement_position(detector_src["placement"])
    detector = cfg["detector"]

    detector["name"] = str(detector_src["name"])
    detector["material"] = _material_name(detector_src["material"])
    detector["shape"] = detector_geometry["shape"]
    detector["thickness_mm"] = float(detector_geometry["thickness_mm"])

    if detector["shape"] == "Circular":
        detector["radius_mm"] = float(detector_geometry["radius_mm"])
    else:
        detector["width_mm"] = float(detector_geometry["width_mm"])
        detector["height_mm"] = float(detector_geometry["height_mm"])

    detector["distance_mm"] = float(detector_position["distance_mm"])
    detector["elevation_deg"] = float(detector_position["elevation_deg"])
    detector["azimuth_deg"] = float(detector_position["azimuth_deg"])

    detector["filters"] = [
        _import_solid_component(item)
        for item in detector_src["detector_filters"]
    ]

    detector["collimators"] = [
        _import_aperture_component(item)
        for item in detector_src["detector_collimators"]
    ]

    detector["internal_masks"] = [
        {
            key: value
            for key, value in _import_aperture_component(item).items()
            if key != "enabled"
        }
        for item in detector_src["internal_masks"]
    ]

    # ========================================================
    # DETECTOR HOUSING
    # ========================================================

    housing_src = detector_src.get("housing")

    if housing_src is None:
        detector["housing"]["enabled"] = False
    else:
        housing_geometry = housing_src["geometry"]
        housing = detector["housing"]

        housing["enabled"] = True
        housing["name"] = str(housing_src["name"])
        housing["aperture_shape"] = housing_geometry["aperture_shape"]
        housing["detector_clearance_mm"] = float(
            housing_geometry["detector_clearance_mm"]
        )
        housing["housing_wall_thickness_mm"] = float(
            housing_geometry["housing_wall_thickness_mm"]
        )
        housing["cavity_wall_thickness_mm"] = float(
            housing_geometry["cavity_wall_thickness_mm"]
        )

        if housing["aperture_shape"] == "Circular":
            housing["aperture_radius_mm"] = float(
                housing_geometry["aperture_radius_mm"]
            )
        else:
            housing["aperture_width_mm"] = float(
                housing_geometry["aperture_width_mm"]
            )
            housing["aperture_height_mm"] = float(
                housing_geometry["aperture_height_mm"]
            )

        housing["housing_material"] = _material_name(
            housing_src["housing_material"]
        )
        housing["cavity_material"] = _material_name(
            housing_src["cavity_wall_material"]
        )
        housing["inner_cavity_medium_material"] = _material_name(
            housing_src["inner_cavity_medium_material"]
        )
        housing["window_material"] = _material_name(
            housing_src["window_material"]
        )
        housing["window_thickness_mm"] = float(
            housing_src["window_thickness_mm"]
        )

    # ========================================================
    # PHYSICS
    # ========================================================

    physics_src = source["physics"]

    # Every frontend physics field is required by the validator, so copy the
    # values directly instead of retaining defaults for absent keys.
    cfg["physics"] = {
        key: copy.deepcopy(physics_src[key])
        for key in cfg["physics"]
    }

    # run/noise are Streamlit execution/post-processing settings and are not
    # part of the exported RoboAI config.json.  They intentionally remain at
    # frontend defaults until the user changes them in Build & run / Results.
    return cfg


# ============================================================
# LOAD CONFIG INTO STREAMLIT
# ============================================================


def load_uploaded_config(source: dict, filename: str | None = None):
    """
    Load only an exported RoboAI config.json.

    The operation is atomic:
      1. validate the uploaded RoboAI structure and canonical keys
      2. convert it to the frontend ui_config
      3. dry-build the RoboAI objects to catch semantic/configuration errors
      4. only then replace st.session_state.ui_config

    If any step fails, the currently active Streamlit configuration is left
    untouched.
    """

    # Conversion performs strict validation first.  No session state has been
    # changed at this point.
    cfg = import_roboaixrf_config(source)

    # Validate that the converted values can actually construct the same
    # RoboAI configuration objects that Build & run will use.  Import locally
    # to keep state.py lightweight during module import.
    from builder import build_configuration

    build_configuration(copy.deepcopy(cfg))

    # Only now is it safe to replace the active configuration.  Stop any old
    # Geant4 process and invalidate any previously compiled simulation first.
    invalidate_simulation()

    st.session_state.ui_config = cfg
    st.session_state.loaded_config_name = filename
    st.session_state.config_was_imported = True
    st.session_state.uploaded_config_raw = copy.deepcopy(source)

    # Explicit-key data editors otherwise keep their old table data across a
    # rerun even though ui_config has changed.
    for key in list(st.session_state.keys()):
        if str(key).endswith("_editor"):
            del st.session_state[key]


