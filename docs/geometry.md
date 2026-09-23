# Geometry

`Geometry` defines the physical shape and dimensions of components in a RoboAI XRF simulation.

All geometry dimensions are given in **millimetres (mm)**.

Import it with:

```python
from roboaixrf import Geometry
```

## Rectangular geometry

Use `Geometry.rectangular()` to create a rectangular solid.

```python
from roboaixrf import Geometry

geometry = Geometry.rectangular(
    width_mm=10.0,
    height_mm=8.0,
    thickness_mm=1.0,
)
```

The parameters are:

* `width_mm` — width of the object in millimetres
* `height_mm` — height of the object in millimetres
* `thickness_mm` — thickness of the object in millimetres

For example:

```text
width      = 10 mm
height     = 8 mm
thickness  = 1 mm
```

A rectangular geometry can be used for components such as samples, filters, and detectors.

Example with a sample:

```python
from roboaixrf import (
    Geometry,
    Material,
    Sample,
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
```

---

## Circular geometry

Use `Geometry.circular()` to create a circular solid.

```python
from roboaixrf import Geometry

geometry = Geometry.circular(
    radius_mm=4.0,
    thickness_mm=1.0,
)
```

The parameters are:

* `radius_mm` — radius of the circular object
* `thickness_mm` — thickness of the object

For example:

```text
radius     = 4 mm
diameter   = 8 mm
thickness  = 1 mm
```

A circular geometry is useful for objects such as circular samples, detector active volumes, and filters.

Example with a detector:

```python
from roboaixrf import (
    Detector,
    Geometry,
    Material,
)

detector = Detector(
    name="silicon_detector",
    material=Material.geant4("G4_Si"),
    geometry=Geometry.circular(
        radius_mm=4.0,
        thickness_mm=1.0,
    ),
)
```

---

# Aperture geometries

Aperture geometries contain an opening through the component.

They are commonly used for:

* collimators
* detector masks
* apertures

RoboAI XRF supports circular and rectangular apertures.

## Circular aperture

Use `Geometry.circular_aperture()` to create a circular opening inside a circular outer body.

```python
from roboaixrf import Geometry

geometry = Geometry.circular_aperture(
    aperture_radius_mm=2.0,
    outer_radius_mm=5.0,
    length_mm=1.0,
)
```

The parameters are:

* `aperture_radius_mm` — radius of the opening
* `outer_radius_mm` — outer radius of the component
* `length_mm` — length or thickness of the component

For example:

```text
outer radius     = 5 mm
aperture radius  = 2 mm
length           = 1 mm
```

The aperture radius must be smaller than the outer radius.

Example with a collimator:

```python
from roboaixrf import (
    Collimator,
    Geometry,
    Material,
    Placement,
)

collimator = Collimator(
    name="tungsten_collimator",
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

---

## Rectangular aperture

Use `Geometry.rectangular_aperture()` to create a rectangular opening inside a rectangular outer body.

```python
from roboaixrf import Geometry

geometry = Geometry.rectangular_aperture(
    aperture_width_mm=3.0,
    aperture_height_mm=2.0,
    outer_width_mm=8.0,
    outer_height_mm=6.0,
    length_mm=1.0,
)
```

The parameters are:

* `aperture_width_mm` — width of the opening
* `aperture_height_mm` — height of the opening
* `outer_width_mm` — total outer width
* `outer_height_mm` — total outer height
* `length_mm` — length or thickness of the component

For example:

```text
outer size      = 8 × 6 mm
aperture size   = 3 × 2 mm
length          = 1 mm
```

Example with a collimator:

```python
from roboaixrf import (
    Collimator,
    Geometry,
    Material,
    Placement,
)

collimator = Collimator(
    name="rectangular_collimator",
    material=Material.geant4("G4_W"),
    geometry=Geometry.rectangular_aperture(
        aperture_width_mm=3.0,
        aperture_height_mm=2.0,
        outer_width_mm=8.0,
        outer_height_mm=6.0,
        length_mm=1.0,
    ),
    placement=Placement.in_front_detector(
        distance_mm=5.0,
    ),
)
```

## Summary

Use:

```python
Geometry.rectangular(...)
```

for rectangular solid objects.

Use:

```python
Geometry.circular(...)
```

for circular solid objects.

Use:

```python
Geometry.circular_aperture(...)
```

for components with a circular opening.

Use:

```python
Geometry.rectangular_aperture(...)
```

for components with a rectangular opening.
