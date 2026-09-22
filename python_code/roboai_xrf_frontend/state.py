from __future__ import annotations

import copy
import hashlib
import json
import os
import signal
import subprocess
from typing import Any

import streamlit as st

from defaults import fresh_default_config


# Session-state values that do not come from DEFAULT_CONFIG.
_STATE_DEFAULTS = {
    "simulation": None,
    "compiled_fingerprint": None,
    "geant4_process": None,
    "geant4_running": False,
    "geant4_stopped": False,
    "geant4_beam_on": None,
    "run_complete": False,
    "noise_result": None,
    "last_root_file": None,
    "loaded_config_name": None,
    "config_was_imported": False,
    "uploaded_config_raw": None,
    "show_docs": False,
}

_ROBOAI_TOP_LEVEL_KEYS = {
    "world",
    "xray_tube",
    "sample",
    "detector",
    "physics",
}

_ALLOWED_ROBOAI_TOP_LEVEL_KEYS = _ROBOAI_TOP_LEVEL_KEYS | {"references_names"}
_FRONTEND_ONLY_TOP_LEVEL_KEYS = {"tube", "run", "noise", "custom_materials"}


class RoboAIConfigValidationError(ValueError):
    """Raised when an uploaded file is not a compatible RoboAI config.json."""


def init_state() -> None:
    """Initialize Streamlit state without overwriting existing values."""
    if "ui_config" not in st.session_state:
        st.session_state.ui_config = fresh_default_config()

    for key, value in _STATE_DEFAULTS.items():
        st.session_state.setdefault(key, value)


def configuration_fingerprint(config: dict) -> str:
    """Return a stable hash for all settings that affect the compiled simulation."""
    payload = {
        key: value
        for key, value in config.items()
        if key not in {"run", "noise"}
    }

    # The run name changes where generated files are stored, so keep it in the
    # fingerprint even though the rest of the run settings are excluded.
    payload["run_name"] = config["run"]["run_name"]

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    return hashlib.sha256(encoded).hexdigest()


def _active_geant4_process():
    """Return the active Popen object, or None if no process is running."""
    process = st.session_state.get("geant4_process")
    if process is None or process.poll() is not None:
        return None
    return process


def _clear_run_results() -> None:
    st.session_state.run_complete = False
    st.session_state.noise_result = None
    st.session_state.last_root_file = None


def _clear_editor_state() -> None:
    """Remove Streamlit data-editor widget state after loading/resetting config."""
    for key in list(st.session_state.keys()):
        if str(key).endswith("_editor"):
            del st.session_state[key]


def stop_geant4_process() -> bool:
    """Stop the running Geant4 process and its process group, if one exists."""
    process = st.session_state.get("geant4_process")

    if process is None:
        st.session_state.geant4_running = False
        return False

    if process.poll() is not None:
        st.session_state.geant4_process = None
        st.session_state.geant4_running = False
        return False

    try:
        # start_run() should launch Geant4 with start_new_session=True so the
        # complete process group can be terminated together.
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait()

    except ProcessLookupError:
        pass

    except Exception:
        # Fallback for a process that was not launched in its own process group.
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
    _clear_run_results()
    return True


def update_geant4_process_state():
    """
    Refresh the stored Geant4 process state.

    Returns:
        None: no stored process
        "running": process is still running
        int: finished process return code
    """
    process = st.session_state.get("geant4_process")

    if process is None:
        st.session_state.geant4_running = False
        return None

    return_code = process.poll()

    if return_code is None:
        st.session_state.geant4_running = True
        return "running"

    st.session_state.geant4_running = False
    st.session_state.geant4_process = None
    return return_code


def invalidate_simulation() -> None:
    """Invalidate compiled/run state, stopping Geant4 first when necessary."""
    if _active_geant4_process() is not None:
        stop_geant4_process()

    st.session_state.simulation = None
    st.session_state.compiled_fingerprint = None
    st.session_state.geant4_process = None
    st.session_state.geant4_running = False
    st.session_state.geant4_stopped = False
    _clear_run_results()


def reset_all() -> None:
    """Restore the complete frontend to its default configuration and state."""
    invalidate_simulation()

    st.session_state.ui_config = fresh_default_config()
    st.session_state.loaded_config_name = None
    st.session_state.config_was_imported = False
    st.session_state.uploaded_config_raw = None

    _clear_editor_state()


# -----------------------------------------------------------------------------
# RoboAI config import helpers
# -----------------------------------------------------------------------------


def _material_name(material: Any, default: str = "G4_Galactic") -> str:
    """Convert an exported material object to the simple frontend material name."""
    if material is None:
        return default

    if isinstance(material, str):
        return material

    if isinstance(material, dict):
        name = material.get("material_name") or material.get("name")
        if name:
            return str(name)

    return default


def _composition_to_string(composition: Any) -> str:
    """Convert exported custom-material composition to 'Cu:0.5,W:0.5'."""
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
        parts: list[str] = []

        for item in composition:
            if not isinstance(item, dict):
                continue

            element = next(
                (
                    item[key]
                    for key in ("element", "symbol", "name")
                    if key in item and item[key] is not None
                ),
                None,
            )
            fraction = next(
                (
                    item[key]
                    for key in ("fraction", "mass_fraction", "value")
                    if key in item and item[key] is not None
                ),
                None,
            )

            if element is not None and fraction is not None:
                parts.append(f"{element}:{fraction}")

        return ",".join(parts)

    return str(composition)


def _collect_custom_materials(config: dict) -> list[dict]:
    """Collect unique embedded custom-material definitions from an export."""
    found: dict[str, dict] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if str(value.get("material_type", "")).lower() == "custom":
                name = value.get("material_name")
                if name:
                    found[str(name)] = {
                        "material_name": str(name),
                        "density_g_cm3": float(
                            value.get("density_g_cm3", value.get("density", 1.0))
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


def _validate_roboaixrf_root(source: dict) -> None:
    """Perform only the small amount of validation the importer itself needs."""
    if not isinstance(source, dict):
        raise RoboAIConfigValidationError(
            "Invalid RoboAI XRF configuration: the JSON root must be an object."
        )

    frontend_keys = sorted(_FRONTEND_ONLY_TOP_LEVEL_KEYS.intersection(source))
    if frontend_keys:
        raise RoboAIConfigValidationError(
            "This is a Streamlit frontend configuration, not an exported "
            "RoboAI config.json. Frontend-only key(s): "
            + ", ".join(frontend_keys)
        )

    missing = sorted(_ROBOAI_TOP_LEVEL_KEYS - set(source))
    if missing:
        raise RoboAIConfigValidationError(
            "Invalid RoboAI XRF configuration. Missing top-level key(s): "
            + ", ".join(missing)
        )

    unexpected = sorted(set(source) - _ALLOWED_ROBOAI_TOP_LEVEL_KEYS)
    if unexpected:
        raise RoboAIConfigValidationError(
            "Invalid RoboAI XRF configuration. Unexpected top-level key(s): "
            + ", ".join(unexpected)
        )


def _placement_position(placement: dict) -> dict:
    """Return Placement.position while supporting the older direct layout."""
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
        "aperture_radius_mm": float(geometry.get("aperture_radius_mm") or 0.0),
        "outer_radius_mm": float(geometry.get("outer_radius_mm") or 0.0),
        "aperture_width_mm": float(geometry.get("aperture_width_mm") or 0.0),
        "aperture_height_mm": float(geometry.get("aperture_height_mm") or 0.0),
        "outer_width_mm": float(geometry.get("outer_width_mm") or 0.0),
        "outer_height_mm": float(geometry.get("outer_height_mm") or 0.0),
        "length_mm": float(geometry["length_mm"]),
        "distance_mm": float(position["distance_mm"]),
    }


def _convert_roboaixrf_config(source: dict) -> dict:
    """Convert an exported RoboAI configuration into the frontend ui_config."""
    _validate_roboaixrf_root(source)
    cfg = fresh_default_config()

    # World
    world_src = source["world"]
    cfg["world"] = {
        "material": _material_name(world_src["world_material"]),
        "size_x_mm": float(world_src["world_size_x_mm"]),
        "size_y_mm": float(world_src["world_size_y_mm"]),
        "size_z_mm": float(world_src["world_size_z_mm"]),
    }

    # Custom materials are embedded in the exported RoboAI object tree.
    cfg["custom_materials"] = _collect_custom_materials(source)

    # Sample
    sample_src = source["sample"]
    sample_geometry = sample_src["geometry"]
    sample = cfg["sample"]

    sample.update(
        {
            "name": str(sample_src["name"]),
            "material": _material_name(sample_src["material"]),
            "shape": sample_geometry["shape"],
            "thickness_mm": float(sample_geometry["thickness_mm"]),
        }
    )

    if sample["shape"] == "Circular":
        sample["radius_mm"] = float(sample_geometry["radius_mm"])
    elif sample["shape"] == "Rectangular":
        sample["width_mm"] = float(sample_geometry["width_mm"])
        sample["height_mm"] = float(sample_geometry["height_mm"])
    else:
        raise RoboAIConfigValidationError(
            f"Unsupported sample geometry shape: {sample['shape']!r}."
        )

    # X-ray tube
    tube_src = source["xray_tube"]
    tube = cfg["tube"]

    tube.update(
        {
            "name": str(tube_src["name"]),
            "current_ma": float(tube_src["current_ma"]),
            "voltage_kv": float(tube_src["voltage_kv"]),
            "anode_angle_deg": float(tube_src["anode_angle_deg"]),
            "anode_symbol": str(tube_src["anode_symbol"]),
            "focal_spot_diameter_mm": float(
                tube_src["focal_spot_diameter_mm"]
            ),
            "tube_collimator_radius_mm": float(
                tube_src["tube_collimator_radius_mm"]
            ),
            "tube_window_to_virtual_collimator_distance_mm": float(
                tube_src["tube_window_to_virtual_collimator_distance_mm"]
            ),
            "tube_type": str(tube_src["tube_type"]),
            "target_thickness_um": float(tube_src["target_thickness_um"]),
        }
    )

    tube_placement = tube_src["placement"]

    if "focal_spot_to_sample_distance_mm" in tube_placement:
        tube.update(
            {
                "focal_spot_to_sample_distance_mm": float(
                    tube_placement["focal_spot_to_sample_distance_mm"]
                ),
                "tube_window_to_sample_distance_mm": float(
                    tube_placement["tube_window_to_sample_distance_mm"]
                ),
                "elevation_deg": float(tube_placement["elevation_deg"]),
                "azimuth_deg": float(tube_placement["azimuth_deg"]),
            }
        )
    else:
        tube_position = tube_placement["position"]
        tube.update(
            {
                "focal_spot_to_sample_distance_mm": float(
                    tube_position["distance_mm"]
                ),
                "tube_window_to_sample_distance_mm": float(
                    tube_src["tube_window_to_sample_distance_mm"]
                ),
                "elevation_deg": float(tube_position["elevation_deg"]),
                "azimuth_deg": float(tube_position["azimuth_deg"]),
            }
        )

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

    tube["geant4_filters"] = [
        _import_solid_component(item)
        for item in tube_src["tube_filters_geant4"]
    ]

    # Detector
    detector_src = source["detector"]
    detector_geometry = detector_src["geometry"]
    detector_position = _placement_position(detector_src["placement"])
    detector = cfg["detector"]

    detector.update(
        {
            "name": str(detector_src["name"]),
            "material": _material_name(detector_src["material"]),
            "shape": detector_geometry["shape"],
            "thickness_mm": float(detector_geometry["thickness_mm"]),
            "distance_mm": float(detector_position["distance_mm"]),
            "elevation_deg": float(detector_position["elevation_deg"]),
            "azimuth_deg": float(detector_position["azimuth_deg"]),
        }
    )

    if detector["shape"] == "Circular":
        detector["radius_mm"] = float(detector_geometry["radius_mm"])
    elif detector["shape"] == "Rectangular":
        detector["width_mm"] = float(detector_geometry["width_mm"])
        detector["height_mm"] = float(detector_geometry["height_mm"])
    else:
        raise RoboAIConfigValidationError(
            f"Unsupported detector geometry shape: {detector['shape']!r}."
        )

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

    # Detector housing
    housing_src = detector_src.get("housing")

    if housing_src is None:
        detector["housing"]["enabled"] = False
    else:
        housing_geometry = housing_src["geometry"]
        housing = detector["housing"]

        housing.update(
            {
                "enabled": True,
                "name": str(housing_src["name"]),
                "aperture_shape": housing_geometry["aperture_shape"],
                "detector_clearance_mm": float(
                    housing_geometry["detector_clearance_mm"]
                ),
                "housing_wall_thickness_mm": float(
                    housing_geometry["housing_wall_thickness_mm"]
                ),
                "cavity_wall_thickness_mm": float(
                    housing_geometry["cavity_wall_thickness_mm"]
                ),
                "housing_material": _material_name(
                    housing_src["housing_material"]
                ),
                "cavity_material": _material_name(
                    housing_src["cavity_wall_material"]
                ),
                "inner_cavity_medium_material": _material_name(
                    housing_src["inner_cavity_medium_material"]
                ),
                "window_material": _material_name(
                    housing_src["window_material"]
                ),
                "window_thickness_mm": float(
                    housing_src["window_thickness_mm"]
                ),
            }
        )

        if housing["aperture_shape"] == "Circular":
            housing["aperture_radius_mm"] = float(
                housing_geometry["aperture_radius_mm"]
            )
        elif housing["aperture_shape"] == "Rectangular":
            housing["aperture_width_mm"] = float(
                housing_geometry["aperture_width_mm"]
            )
            housing["aperture_height_mm"] = float(
                housing_geometry["aperture_height_mm"]
            )
        else:
            raise RoboAIConfigValidationError(
                "Unsupported detector housing aperture shape: "
                f"{housing['aperture_shape']!r}."
            )

    # Physics. run/noise remain frontend defaults because they are not part of
    # the exported RoboAI configuration.
    physics_src = source["physics"]
    cfg["physics"] = {
        key: copy.deepcopy(physics_src[key])
        for key in cfg["physics"]
    }

    return cfg


def import_roboaixrf_config(source: dict) -> dict:
    """
    Convert an exported RoboAI config.json into frontend ui_config.

    Structural mistakes are reported as RoboAIConfigValidationError. Semantic
    model validation happens in load_uploaded_config() through the same
    build_configuration() path used by Build & run.
    """
    try:
        return _convert_roboaixrf_config(source)
    except RoboAIConfigValidationError:
        raise
    except KeyError as exc:
        raise RoboAIConfigValidationError(
            f"Invalid RoboAI XRF configuration. Missing required key: {exc.args[0]!r}."
        ) from exc
    except (TypeError, ValueError) as exc:
        raise RoboAIConfigValidationError(
            f"Invalid RoboAI XRF configuration: {exc}"
        ) from exc


def validate_roboaixrf_config(source: dict) -> None:
    """
    Validate that an exported RoboAI config can be converted by this frontend.

    Kept as a public function for compatibility with existing imports. The
    previous ~900-line duplicate schema validator is intentionally removed.
    """
    import_roboaixrf_config(source)


def load_uploaded_config(source: dict, filename: str | None = None) -> None:
    """
    Atomically load an exported RoboAI config.json into Streamlit state.

    The active configuration is changed only after conversion and a dry build
    both succeed.
    """
    cfg = import_roboaixrf_config(source)

    # Import locally so state.py stays lightweight at module import time.
    from builder import build_configuration

    # This is the real semantic validation: construct the same RoboAI objects
    # that Build & run will use before touching the current session state.
    build_configuration(copy.deepcopy(cfg))

    invalidate_simulation()

    st.session_state.ui_config = cfg
    st.session_state.loaded_config_name = filename
    st.session_state.config_was_imported = True
    st.session_state.uploaded_config_raw = copy.deepcopy(source)

    _clear_editor_state()
