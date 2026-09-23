# X-ray Tube

`XRayTube` defines the X-ray source used in the XRF simulation.

An X-ray tube contains information such as:

* tube voltage
* tube current
* anode material
* anode angle
* focal spot size
* tube position
* virtual collimator size
* tube window

Import the required classes with:

```python
from roboaixrf import (
    XRayTube,
    TubePlacement,
    TubeWindow,
    Material,
)
```

## Creating the tube placement

Before creating an X-ray tube, define its position relative to the sample using `TubePlacement`.

```python
from roboaixrf import TubePlacement

tube_placement = TubePlacement(
    focal_spot_to_sample_distance_mm=140.0,
    tube_window_to_sample_distance_mm=130.0,
    elevation_deg=90.0,
    azimuth_deg=0.0,
)
```

### Parameters

`focal_spot_to_sample_distance_mm`

Distance between the X-ray tube focal spot and the sample.

```text
focal spot
    |
    | 140 mm
    |
    v
 sample
```

`tube_window_to_sample_distance_mm`

Distance between the tube window and the sample.

```text
tube window
     |
     | 130 mm
     |
     v
   sample
```

`elevation_deg`

Elevation angle of the X-ray tube relative to the sample.

`azimuth_deg`

Azimuth angle of the X-ray tube around the sample.

---

# Creating an X-ray tube

An `XRayTube` should be created using:

```python
XRayTube.create(...)
```

Example:

```python
from roboaixrf import (
    XRayTube,
    TubePlacement,
)

tube_placement = TubePlacement(
    focal_spot_to_sample_distance_mm=140.0,
    tube_window_to_sample_distance_mm=130.0,
    elevation_deg=90.0,
    azimuth_deg=0.0,
)

tube = XRayTube.create(
    name="xray_tube",
    current_ma=1.0,
    voltage_kv=50.0,
    anode_angle_deg=15.0,
    anode_symbol="W",
    focal_spot_diameter_mm=0.05,
    tube_collimator_radius_mm=3.0,
    tube_window_to_virtual_collimator_distance_mm=10.0,
    tube_placement=tube_placement,
)
```

Do not create the tube directly with:

```python
XRayTube(...)
```

Use:

```python
XRayTube.create(...)
```

instead.

---

# Tube operating parameters

## `current_ma`

The tube current is specified in milliamperes.

```python
current_ma=1.0
```

means:

```text
tube current = 1.0 mA
```

---

## `voltage_kv`

The tube voltage is specified in kilovolts.

```python
voltage_kv=50.0
```

means:

```text
tube voltage = 50 kV
```

---

## `anode_angle_deg`

Defines the X-ray tube anode angle.

```python
anode_angle_deg=15.0
```

means:

```text
anode angle = 15°
```

---

## `anode_symbol`

Defines the element used as the tube target.

For example:

```python
anode_symbol="W"
```

uses tungsten as the target material.

The currently supported SpekPy target symbols are:

```text
Cr
Cu
Mo
Rh
Ag
W
Au
```

For example, a tungsten tube uses:

```python
anode_symbol="W"
```

while a silver tube uses:

```python
anode_symbol="Ag"
```

---

# Focal spot

`focal_spot_diameter_mm` defines the diameter of the X-ray source focal spot.

For example:

```python
focal_spot_diameter_mm=0.05
```

means:

```text
focal spot diameter = 0.05 mm
```

---

# Virtual tube collimator

The X-ray source also uses a virtual collimator.

Its radius is defined with:

```python
tube_collimator_radius_mm=3.0
```

and its distance from the tube window is defined with:

```python
tube_window_to_virtual_collimator_distance_mm=10.0
```

For example:

```text
tube window
     |
     | 10 mm
     |
     v
virtual collimator
```

The virtual collimator radius must be greater than zero.

---

# Tube window

The tube window is created separately using `TubeWindow`.

Example:

```python
from roboaixrf import (
    TubeWindow,
    Material,
)

window = TubeWindow(
    name="beryllium_window",
    material=Material.geant4("G4_Be"),
    thickness_mm=0.01,
)
```

This creates a beryllium window with:

```text
material  = Be
thickness = 0.01 mm
```

Attach the window to the tube with:

```python
tube.set_window(window)
```

---

# Complete example

A complete basic X-ray tube can therefore be created like this:

```python
from roboaixrf import (
    XRayTube,
    TubePlacement,
    TubeWindow,
    Material,
)

# Position of the X-ray tube
tube_placement = TubePlacement(
    focal_spot_to_sample_distance_mm=140.0,
    tube_window_to_sample_distance_mm=130.0,
    elevation_deg=90.0,
    azimuth_deg=0.0,
)

# Create the X-ray tube
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

# Create the tube window
window = TubeWindow(
    name="beryllium_window",
    material=Material.geant4("G4_Be"),
    thickness_mm=0.01,
)

# Attach the window to the tube
tube.set_window(window)

# Check that the required tube components exist
tube.validate_complete()
```

The resulting tube now contains its operating parameters, physical placement, virtual collimator, and tube window.

Filters can also be added to the X-ray tube. They are covered separately in the filter documentation.
