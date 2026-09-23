# Placement

`Placement` defines **where a component is located** and **how it is oriented** in the XRF simulation.

Import it with:

```python
from roboaixrf import Placement
```

You normally should **not create `Placement` directly**.

Instead, use one of the provided placement methods:

```python
Placement.face_sample(...)
Placement.manual(...)
Placement.in_front_detector(...)
Placement.in_front_of_tube_window(...)
```

---

## `Placement.face_sample()`

Use `face_sample()` to place a component at a given distance and angle relative to the sample while automatically orienting the component toward the sample.

```python
from roboaixrf import Placement

placement = Placement.face_sample(
    distance_mm=17.0,
    elevation_deg=90.0,
    azimuth_deg=50.0,
)
```

### Parameters

* `distance_mm` — distance from the sample in millimetres
* `elevation_deg` — elevation angle in degrees
* `azimuth_deg` — azimuth angle in degrees

For example:

```text
distance  = 17 mm
elevation = 90°
azimuth   = 50°
```

This placement mode is useful for components such as detectors.

### Example with a detector

```python
from roboaixrf import (
    Detector,
    Geometry,
    Material,
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

The detector is positioned 17 mm from the sample and automatically oriented so that its active face points toward the sample.

---

## `Placement.manual()`

Use `manual()` when you want to control both the position and orientation yourself.

```python
from roboaixrf import Placement

placement = Placement.manual(
    distance_mm=20.0,
    elevation_deg=60.0,
    azimuth_deg=30.0,
    x=0.0,
    y=0.0,
    z=1.0,
)
```

### Position parameters

The position is defined by:

* `distance_mm`
* `elevation_deg`
* `azimuth_deg`

### Orientation parameters

The manual orientation is defined by:

* `x`
* `y`
* `z`

For example:

```text
Position:

distance  = 20 mm
elevation = 60°
azimuth   = 30°

Orientation:

x = 0
y = 0
z = 1
```

Use manual placement when `face_sample()` does not provide the orientation required for the component.

---

## `Placement.in_front_detector()`

Use `in_front_detector()` for components positioned directly in front of the detector.

```python
from roboaixrf import Placement

placement = Placement.in_front_detector(
    distance_mm=3.0,
)
```

Only the distance from the detector needs to be specified.

The component inherits the detector orientation.

This is useful for:

* detector filters
* detector collimators
* internal detector masks

### Example with a detector filter

```python
from roboaixrf import (
    Filter,
    Geometry,
    Material,
    Placement,
)

detector_filter = Filter(
    name="aluminium_filter",
    material=Material.geant4("G4_Al"),
    geometry=Geometry.circular(
        radius_mm=5.0,
        thickness_mm=0.5,
    ),
    placement=Placement.in_front_detector(
        distance_mm=3.0,
    ),
)
```

Here the filter is positioned 3 mm in front of the detector.

Its orientation follows the detector automatically.

---

## `Placement.in_front_of_tube_window()`

Use `in_front_of_tube_window()` for a component positioned relative to the X-ray tube window.

```python
from roboaixrf import Placement

placement = Placement.in_front_of_tube_window(
    distance_mm=5.0,
)
```

The distance is measured from the tube window.

This placement is intended for components such as physical X-ray tube filters.

For example:

```python
from roboaixrf import (
    Filter,
    Geometry,
    Material,
    Placement,
)

tube_filter = Filter(
    name="aluminium_tube_filter",
    material=Material.geant4("G4_Al"),
    geometry=Geometry.circular(
        radius_mm=5.0,
        thickness_mm=0.5,
    ),
    placement=Placement.in_front_of_tube_window(
        distance_mm=5.0,
    ),
)
```

The filter is positioned 5 mm in front of the X-ray tube window.

---

# Position

Internally, a `Placement` contains a `Position`.

A position contains:

```text
reference
distance_mm
elevation_deg
azimuth_deg
```

For example, `Placement.face_sample()` creates a position whose reference is:

```text
sample
```

while:

```python
Placement.in_front_detector(...)
```

uses:

```text
detector
```

as its reference.

Normally you do not need to create `Position` manually because the placement methods create it automatically.

---

# Orientation

A `Placement` can also contain an `Orientation`.

The orientation mode depends on the placement method.

`Placement.face_sample()` uses:

```text
face_sample
```

`Placement.manual()` uses:

```text
manual
```

and components placed in front of another component use an inherited orientation.

Normally you do not need to create `Orientation` separately.

---

# Which placement should I use?

Use:

```python
Placement.face_sample(...)
```

when a component should be positioned relative to the sample and point toward it.

Use:

```python
Placement.manual(...)
```

when you need to specify the orientation yourself.

Use:

```python
Placement.in_front_detector(...)
```

when adding something such as a filter, mask, or collimator in front of the detector.

Use:

```python
Placement.in_front_of_tube_window(...)
```

when adding a physical component in front of the X-ray tube window.
