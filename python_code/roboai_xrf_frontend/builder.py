from __future__ import annotations

import math
from pathlib import Path

from roboaixrf import (
    XRFConfigure,
    Material,
    Composition,
    Placement,
    Orientation,
    Geometry,
    XRayTube,
    TubePlacement,
    TubeWindow,
    Filter,
    Collimator,
    Sample,
    Detector,
    Housing,
    Internal_mask,
    Physics,
    RoboAiXrfSimulation,
)


def _parse_composition(text: str) -> list[Composition]:
    items = []
    for raw in text.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if ":" not in raw:
            raise ValueError(
                f"Invalid composition item '{raw}'. Use Element:fraction, e.g. Cu:0.5,W:0.5"
            )
        element, fraction = raw.split(":", 1)
        items.append(
            Composition(
                element=element.strip(),
                mass_fraction=float(fraction.strip()),
            )
        )

    if not items:
        raise ValueError("A custom material must contain at least one element.")

    total = sum(item.mass_fraction for item in items)
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"Custom-material mass fractions must sum to 1.0; got {total:g}")

    # The package currently checks `total != 1.0` exactly.
    # Correct the final value for harmless floating-point representation drift.
    if len(items) > 1:
        previous = sum(item.mass_fraction for item in items[:-1])
        items[-1].mass_fraction = 1.0 - previous

    return items


def build_material(material_name: str, custom_materials: list[dict]) -> Material:
    material_name = material_name.strip()

    if material_name.startswith("G4_"):
        return Material.geant4(material_name)

    for spec in custom_materials:
        if spec["material_name"].strip() == material_name:
            return Material.custom_mat(
                density_g_cm3=float(spec["density_g_cm3"]),
                compositions=_parse_composition(spec["composition"]),
                material_name=material_name,
            )

    raise ValueError(
        f"Unknown material '{material_name}'. Use a Geant4 material such as G4_Fe "
        "or define it on the Materials page."
    )


def _solid_geometry(spec: dict) -> Geometry:
    if spec["shape"] == "Circular":
        return Geometry.circular(
            radius_mm=float(spec["radius_mm"]),
            thickness_mm=float(spec["thickness_mm"]),
        )

    if spec["shape"] == "Rectangular":
        return Geometry.rectangular(
            width_mm=float(spec["width_mm"]),
            height_mm=float(spec["height_mm"]),
            thickness_mm=float(spec["thickness_mm"]),
        )

    raise ValueError(f"Unsupported solid geometry: {spec['shape']}")


def _aperture_geometry(spec: dict) -> Geometry:
    if spec["aperture_shape"] == "Circular":
        return Geometry.circular_aperture(
            aperture_radius_mm=float(spec["aperture_radius_mm"]),
            outer_radius_mm=float(spec["outer_radius_mm"]),
            length_mm=float(spec["length_mm"]),
        )

    if spec["aperture_shape"] == "Rectangular":
        return Geometry.rectangular_aperture(
            aperture_width_mm=float(spec["aperture_width_mm"]),
            aperture_height_mm=float(spec["aperture_height_mm"]),
            outer_width_mm=float(spec["outer_width_mm"]),
            outer_height_mm=float(spec["outer_height_mm"]),
            length_mm=float(spec["length_mm"]),
        )

    raise ValueError(f"Unsupported aperture geometry: {spec['aperture_shape']}")


def _front_of_tube_window(distance_mm: float) -> Placement:
    placement = Placement.in_front_of_tube_window(distance_mm=float(distance_mm))

    # Package workaround:
    # Placement.in_front_of_tube_window() currently constructs its input using
    # "Orientation" instead of the model field "orientation".
    if placement.orientation is None:
        placement.orientation = Orientation(mode="inherient")

    return placement


def build_world(config: dict) -> XRFConfigure:
    world_spec = config["world"]
    custom = config["custom_materials"]

    world = XRFConfigure(
        world_material=build_material(world_spec["material"], custom),
        world_size_x_mm=float(world_spec["size_x_mm"]),
        world_size_y_mm=float(world_spec["size_y_mm"]),
        world_size_z_mm=float(world_spec["size_z_mm"]),
    )

    world.physics = Physics(**config["physics"])
    return world


def build_sample(config: dict) -> Sample:
    spec = config["sample"]
    return Sample(
        name=spec["name"],
        geometry=_solid_geometry(spec),
        material=build_material(spec["material"], config["custom_materials"]),
    )


def build_tube(config: dict) -> XRayTube:
    spec = config["tube"]
    custom = config["custom_materials"]

    tube_placement = TubePlacement(
        focal_spot_to_sample_distance_mm=float(
            spec["focal_spot_to_sample_distance_mm"]
        ),
        tube_window_to_sample_distance_mm=float(
            spec["tube_window_to_sample_distance_mm"]
        ),
        elevation_deg=float(spec["elevation_deg"]),
        azimuth_deg=float(spec["azimuth_deg"]),
    )

    tube = XRayTube.create(
        name=spec["name"],
        current_ma=float(spec["current_ma"]),
        voltage_kv=float(spec["voltage_kv"]),
        anode_angle_deg=float(spec["anode_angle_deg"]),
        anode_symbol=spec["anode_symbol"],
        focal_spot_diameter_mm=float(spec["focal_spot_diameter_mm"]),
        tube_collimator_radius_mm=float(spec["tube_collimator_radius_mm"]),
        tube_window_to_virtual_collimator_distance_mm=float(
            spec["tube_window_to_virtual_collimator_distance_mm"]
        ),
        tube_placement=tube_placement,
    )

    tube.tube_type = spec["tube_type"]
    tube.target_thickness_um = float(spec["target_thickness_um"])

    window_spec = spec["window"]
    tube.set_window(
        TubeWindow(
            name=window_spec["name"],
            material=build_material(window_spec["material"], custom),
            thickness_mm=float(window_spec["thickness_mm"]),
        )
    )

    for item in spec["spekpy_filters"]:
        if not str(item.get("element", "")).strip():
            continue
        tube.add_filter_spekpy(
            {
                "element": str(item["element"]).strip(),
                "thickness_mm": float(item["thickness_mm"]),
            }
        )

    for item in spec["geant4_filters"]:
        if not bool(item.get("enabled", True)):
            continue

        geometry = _solid_geometry(item)
        tube_filter = Filter(
            name=str(item["name"]),
            geometry=geometry,
            material=build_material(str(item["material"]), custom),
            placement=_front_of_tube_window(float(item["distance_mm"])),
        )
        tube.add_filter_geant4(tube_filter)

    return tube


def _build_housing(detector: Detector, config: dict):
    spec = config["detector"]["housing"]
    if not spec["enabled"]:
        return

    if spec["aperture_shape"] == "Circular":
        geometry = Geometry.detector_housing_circular_aperture(
            aperture_radius_mm=float(spec["aperture_radius_mm"]),
            detector_clearance_mm=float(spec["detector_clearance_mm"]),
            housing_wall_thickness_mm=float(spec["housing_wall_thickness_mm"]),
            cavity_wall_thickness_mm=float(spec["cavity_wall_thickness_mm"]),
        )
    else:
        geometry = Geometry.detector_housing_rectangular_aperture(
            aperture_width_mm=float(spec["aperture_width_mm"]),
            aperture_height_mm=float(spec["aperture_height_mm"]),
            detector_clearance_mm=float(spec["detector_clearance_mm"]),
            housing_wall_thickness_mm=float(spec["housing_wall_thickness_mm"]),
            cavity_wall_thickness_mm=float(spec["cavity_wall_thickness_mm"]),
        )

    custom = config["custom_materials"]
    housing = Housing.create(
        name=spec["name"],
        geometry=geometry,
        housing_material=build_material(spec["housing_material"], custom),
        cavity_material=build_material(spec["cavity_material"], custom),
        inner_cavity_medium_material=build_material(
            spec["inner_cavity_medium_material"], custom
        ),
        window_material=build_material(spec["window_material"], custom),
        window_thickness_mm=float(spec["window_thickness_mm"]),
    )
    detector.add_housing(housing)


def _build_internal_masks(detector: Detector, config: dict):
    if not config["detector"]["housing"]["enabled"]:
        if config["detector"]["internal_masks"]:
            raise ValueError("Internal masks require detector housing to be enabled.")
        return

    custom = config["custom_materials"]
    for item in config["detector"]["internal_masks"]:
        if not str(item.get("name", "")).strip():
            continue
        mask = Internal_mask(
            name=str(item["name"]),
            geometry=_aperture_geometry(item),
            material=build_material(str(item["material"]), custom),
            placement=Placement.in_front_detector(float(item["distance_mm"])),
        )
        detector.add_internal_mask(mask)


def _build_detector_filters(detector: Detector, config: dict):
    custom = config["custom_materials"]
    for item in config["detector"]["filters"]:
        if not bool(item.get("enabled", True)):
            continue
        detector.add_filter(
            Filter(
                name=str(item["name"]),
                geometry=_solid_geometry(item),
                material=build_material(str(item["material"]), custom),
                placement=Placement.in_front_detector(float(item["distance_mm"])),
            )
        )


def _build_detector_collimators(detector: Detector, config: dict):
    custom = config["custom_materials"]
    for item in config["detector"]["collimators"]:
        if not bool(item.get("enabled", True)):
            continue
        detector.add_collimator(
            Collimator(
                name=str(item["name"]),
                geometry=_aperture_geometry(item),
                material=build_material(str(item["material"]), custom),
                placement=Placement.in_front_detector(float(item["distance_mm"])),
            )
        )


def build_detector(config: dict) -> Detector:
    spec = config["detector"]

    detector = Detector(
        name=spec["name"],
        geometry=_solid_geometry(spec),
        material=build_material(spec["material"], config["custom_materials"]),
        placement=Placement.face_sample(
            distance_mm=float(spec["distance_mm"]),
            elevation_deg=float(spec["elevation_deg"]),
            azimuth_deg=float(spec["azimuth_deg"]),
        ),
    )

    _build_housing(detector, config)
    _build_internal_masks(detector, config)
    _build_detector_filters(detector, config)
    _build_detector_collimators(detector, config)
    return detector


def build_configuration(config: dict) -> XRFConfigure:
    world = build_world(config)
    world.add(build_sample(config))
    world.add(build_detector(config))
    world.add(build_tube(config))
    world.validate_complete()
    return world


def build_simulation(config: dict, runs_root: str | Path = "runs") -> RoboAiXrfSimulation:
    run_name = str(config["run"]["run_name"]).strip()
    if not run_name:
        raise ValueError("Run name cannot be empty.")

    run_path = Path(runs_root) / run_name

    return RoboAiXrfSimulation(
        config=build_configuration(config),
        config_path=run_path,
    )
