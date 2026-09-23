# Detector

`Detector` defines the active detector volume used to record X-rays in the simulation.

A detector requires:

* a name
* a material
* a geometry
* a placement

Import the required classes with:

```python
from roboaixrf import (
    Detector,
    Material,
    Geometry,
    Placement,
)
```

---

# Basic detector

A simple silicon detector can be created like this:

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
```

This creates a circular silicon detector with:

```text
radius     = 4 mm
thickness  = 1 mm
distance   = 17 mm from the sample
elevation  = 90°
azimuth    = 50°
```

---

# Detector material

The detector material defines the active detection medium.

For example, a silicon detector uses:

```python
Material.geant4("G4_Si")
```

Example:

```python
silicon = Material.geant4(
    "G4_Si"
)

detector = Detector(
    name="silicon_detector",
    material=silicon,
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
```

---

# Detector geometry

A detector can currently use two geometry types:

```python
Geometry.circular(...)
```

or:

```python
Geometry.rectangular(...)
```

Aperture geometries cannot be used as the active detector geometry.

---

## Circular detector

```python
detector = Detector(
    name="circular_detector",
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
```

The geometry parameters are:

* `radius_mm`
* `thickness_mm`

---

## Rectangular detector

```python
detector = Detector(
    name="rectangular_detector",
    material=Material.geant4("G4_Si"),
    geometry=Geometry.rectangular(
        width_mm=8.0,
        height_mm=8.0,
        thickness_mm=1.0,
    ),
    placement=Placement.face_sample(
        distance_mm=17.0,
        elevation_deg=90.0,
        azimuth_deg=50.0,
    ),
)
```

The geometry parameters are:

* `width_mm`
* `height_mm`
* `thickness_mm`

---

# Detector placement

The detector is normally positioned relative to the sample using:

```python
Placement.face_sample(...)
```

Example:

```python
placement = Placement.face_sample(
    distance_mm=17.0,
    elevation_deg=90.0,
    azimuth_deg=50.0,
)
```

This places the detector relative to the sample and automatically orients the detector face toward the sample.

---

# Adding a detector filter

A physical filter can be placed in front of the detector.

First create the filter:

```python
from roboaixrf import (
    Filter,
    Material,
    Geometry,
    Placement,
)

detector_filter = Filter(
    name="aluminium_detector_filter",
    material=Material.geant4("G4_Al"),
    geometry=Geometry.circular(
        radius_mm=5.0,
        thickness_mm=0.1,
    ),
    placement=Placement.in_front_detector(
        distance_mm=3.0,
    ),
)
```

Then add it to the detector:

```python
detector.add_filter(
    detector_filter
)
```

Detector filters must use:

```python
Placement.in_front_detector(...)
```

because their position is defined relative to the detector.

---

# Adding a detector collimator

A collimator can also be positioned in front of the detector.

Example:

```python
from roboaixrf import (
    Collimator,
    Material,
    Geometry,
    Placement,
)

collimator = Collimator(
    name="detector_collimator",
    material=Material.geant4("G4_W"),
    geometry=Geometry.circular_aperture(
        aperture_radius_mm=2.0,
        outer_radius_mm=5.0,
        length_mm=1.0,
    ),
    placement=Placement.in_front_detector(
        distance_mm=5.0,
    ),
)
```

Add it to the detector with:

```python
detector.add_collimator(
    collimator
)
```

Like detector filters, detector collimators must be positioned relative to the detector.

---

# Adding a housing

A detector can optionally contain a housing.

After creating a `Housing` object, attach it with:

```python
detector.add_housing(
    housing
)
```

The housing is created separately because it has its own:

* geometry
* housing material
* cavity wall material
* cavity medium
* entrance window

Housing configuration is covered in the detector housing documentation.

---

# Adding an internal mask

Internal masks can be added inside the detector assembly.

For example:

```python
from roboaixrf import (
    Internal_mask,
    Material,
    Geometry,
    Placement,
)

mask = Internal_mask(
    name="tungsten_mask",
    material=Material.geant4("G4_W"),
    geometry=Geometry.circular_aperture(
        aperture_radius_mm=2.0,
        outer_radius_mm=5.0,
        length_mm=0.1,
    ),
    placement=Placement.in_front_detector(
        distance_mm=1.0,
    ),
)
```

Then add it with:

```python
detector.add_internal_mask(
    mask
)
```

A detector housing must already exist before an internal mask can be added.

For example:

```python
detector.add_housing(
    housing
)

detector.add_internal_mask(
    mask
)
```

Trying to add an internal mask without a housing will raise an error.

---

# Complete basic detector example

```python
from roboaixrf import (
    Detector,
    Material,
    Geometry,
    Placement,
    Filter,
)

# Create the active detector
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

# Create a detector filter
detector_filter = Filter(
    name="aluminium_filter",
    material=Material.geant4("G4_Al"),
    geometry=Geometry.circular(
        radius_mm=5.0,
        thickness_mm=0.1,
    ),
    placement=Placement.in_front_detector(
        distance_mm=3.0,
    ),
)

# Attach the filter
detector.add_filter(
    detector_filter
)
```

The detector now contains:

```text
Active detector:
    material = Si
    radius = 4 mm
    thickness = 1 mm

Placement:
    distance = 17 mm
    elevation = 90°
    azimuth = 50°

Detector filter:
    material = Al
    thickness = 0.1 mm
```

More advanced detector components such as the housing, internal masks, and detailed collimators are documented separately.
