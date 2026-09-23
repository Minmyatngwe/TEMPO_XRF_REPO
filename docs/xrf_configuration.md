# XRF Configuration

`XRFConfigure` is the main configuration object for an XRF simulation.

It combines:

* world settings
* sample
* detector
* X-ray tube
* physics settings

Import it with:

```python
from roboaixrf import XRFConfigure
```

---

# Creating the world

Every `XRFConfigure` requires a world material and world dimensions.

For example:

```python
from roboaixrf import (
    XRFConfigure,
    Material,
)

config = XRFConfigure(
    world_material=Material.geant4("G4_AIR"),
    world_size_x_mm=300.0,
    world_size_y_mm=300.0,
    world_size_z_mm=300.0,
)
```

This creates a simulation world with:

```text
material = air

size:
    x = 300 mm
    y = 300 mm
    z = 300 mm
```

---

# World material

The world material is specified using:

```python
world_material=Material.geant4("G4_AIR")
```

For example, an air-filled world can use:

```python
Material.geant4("G4_AIR")
```

A vacuum world can instead use:

```python
Material.geant4("G4_Galactic")
```

Choose the world material according to the physical environment you want to simulate.

---

# World dimensions

The world dimensions are defined separately:

```python
world_size_x_mm=300.0
world_size_y_mm=300.0
world_size_z_mm=300.0
```

All values are specified in millimetres.

The world should be large enough to contain the sample, detector, X-ray tube, filters, collimators, and other simulation components.

---

# Adding the sample

After creating the configuration, add a sample with:

```python
config.add(sample)
```

For example:

```python
from roboaixrf import (
    Sample,
    Material,
    Geometry,
)

sample = Sample(
    name="iron_sample",
    material=Material.geant4("G4_Fe"),
    geometry=Geometry.rectangular(
        width_mm=10.0,
        height_mm=10.0,
        thickness_mm=1.0,
    ),
)

config.add(sample)
```

`XRFConfigure` recognizes that the object is a `Sample` and stores it as:

```python
config.sample
```

---

# Adding the detector

A detector is added in the same way:

```python
config.add(detector)
```

Example:

```python
from roboaixrf import (
    Detector,
    Material,
    Geometry,
    Placement,
)

detector = Detector(
    name="silicon_detector",
    material=Material.geant4("G4_Si"),
    geometry=Geometry.circular(
        radius_mm=4.0,
        thickness_mm=1.0,
    ),
    placement=Placement.face_sample(
        distance_mm=17.0,
        elevation_deg=90.0,
        azimuth_deg=50.0,
    ),
)

config.add(detector)
```

The detector is stored as:

```python
config.detector
```

---

# Adding the X-ray tube

The X-ray tube is also added with:

```python
config.add(tube)
```

For example:

```python
config.add(tube)
```

The tube is stored as:

```python
config.xray_tube
```

---

# Adding components with `add()`

The current `add()` method supports:

```text
Sample
Detector
XRayTube
```

For example:

```python
config.add(sample)
config.add(detector)
config.add(tube)
```

The object type determines where it is stored automatically.

You do not need to write:

```python
config.sample = sample
config.detector = detector
config.xray_tube = tube
```

when using `add()`.

---

# Physics configuration

`Physics` is handled differently.

It should not be added with:

```python
config.add(physics)
```

Instead, provide it when creating `XRFConfigure`:

```python
from roboaixrf import (
    XRFConfigure,
    Material,
    Physics,
)

physics = Physics(
    flu_use=True,
    auger_use=True,
)

config = XRFConfigure(
    world_material=Material.geant4("G4_AIR"),
    world_size_x_mm=300.0,
    world_size_y_mm=300.0,
    world_size_z_mm=300.0,
    physics=physics,
)
```

You can also assign it afterwards:

```python
config.physics = physics
```

If no physics configuration is supplied, `XRFConfigure` uses the default `Physics()` configuration.

---

# Validating the configuration

After adding the main components, call:

```python
config.validate_complete()
```

Example:

```python
config.add(sample)
config.add(detector)
config.add(tube)

config.validate_complete()
```

The current validation checks that the configuration contains:

```text
sample
detector
X-ray tube
```

If one is missing, a `ValueError` is raised.

For example, if no detector has been added:

```text
ValueError: Detector is missing
```

If no sample has been added:

```text
ValueError: Sample is missing
```

If no X-ray tube has been added:

```text
ValueError: Tube is missing
```

---

# Complete configuration example

The following example shows how the main objects are combined.

```python
from roboaixrf import (
    XRFConfigure,
    Material,
    Geometry,
    Sample,
    Detector,
    Placement,
    XRayTube,
    TubePlacement,
    TubeWindow,
    Physics,
)

# -------------------------------------------------
# 1. Physics
# -------------------------------------------------

physics = Physics(
    flu_use=True,
    auger_use=True,
    pixe_use=False,
)

# -------------------------------------------------
# 2. World
# -------------------------------------------------

config = XRFConfigure(
    world_material=Material.geant4("G4_AIR"),
    world_size_x_mm=300.0,
    world_size_y_mm=300.0,
    world_size_z_mm=300.0,
    physics=physics,
)

# -------------------------------------------------
# 3. Sample
# -------------------------------------------------

sample = Sample(
    name="iron_sample",
    material=Material.geant4("G4_Fe"),
    geometry=Geometry.rectangular(
        width_mm=10.0,
        height_mm=10.0,
        thickness_mm=1.0,
    ),
)

config.add(sample)

# -------------------------------------------------
# 4. Detector
# -------------------------------------------------

detector = Detector(
    name="silicon_detector",
    material=Material.geant4("G4_Si"),
    geometry=Geometry.circular(
        radius_mm=4.0,
        thickness_mm=1.0,
    ),
    placement=Placement.face_sample(
        distance_mm=17.0,
        elevation_deg=90.0,
        azimuth_deg=50.0,
    ),
)

config.add(detector)

# -------------------------------------------------
# 5. X-ray tube placement
# -------------------------------------------------

tube_placement = TubePlacement(
    focal_spot_to_sample_distance_mm=140.0,
    tube_window_to_sample_distance_mm=130.0,
    elevation_deg=90.0,
    azimuth_deg=0.0,
)

# -------------------------------------------------
# 6. X-ray tube
# -------------------------------------------------

tube = XRayTube.create(
    name="tungsten_tube",
    current_ma=1.0,
    voltage_kv=50.0,
    anode_angle_deg=15.0,
    anode_symbol="W",
    focal_spot_diameter_mm=0.05,
    tube_collimator_radius_mm=3.0,
    tube_window_to_virtual_collimator_distance_mm=10.0,
    tube_placement=tube_placement,
)

# -------------------------------------------------
# 7. Tube window
# -------------------------------------------------

window = TubeWindow(
    name="beryllium_window",
    material=Material.geant4("G4_Be"),
    thickness_mm=0.01,
)

tube.set_window(window)

config.add(tube)

# -------------------------------------------------
# 8. Validate
# -------------------------------------------------

config.validate_complete()

print("XRF configuration is complete.")
```

The resulting configuration contains:

```text
XRFConfigure
│
├── World
│   ├── material
│   └── dimensions
│
├── Physics
│
├── Sample
│
├── Detector
│
└── X-ray tube
    └── Tube window
```

This `config` object can now be passed to `RoboAiXrfSimulation`.
