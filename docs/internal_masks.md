# Internal Masks

`Internal_mask` represents a physical mask located inside the detector assembly.

Internal masks can be used to restrict which photons can reach the active detector area.

Import the required classes with:

```python
from roboaixrf import (
    Internal_mask,
    Material,
    Geometry,
    Placement,
)
```

An internal mask requires:

* a name
* a material
* a geometry
* a placement

---

# Creating an internal mask

A common internal mask uses an aperture geometry.

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

This creates a tungsten mask with:

```text
aperture radius = 2 mm
outer radius    = 5 mm
length          = 0.1 mm
distance        = 1 mm from the detector
```

---

# Placement

Internal masks must use:

```python
Placement.in_front_detector(...)
```

For example:

```python
placement = Placement.in_front_detector(
    distance_mm=1.0,
)
```

The distance is measured relative to the detector.

Using a placement referenced to the sample or X-ray tube is not valid for an internal detector mask.

---

# Circular aperture mask

A circular aperture mask can be created with:

```python
Geometry.circular_aperture(...)
```

Example:

```python
mask = Internal_mask(
    name="circular_mask",
    material=Material.geant4("G4_W"),
    geometry=Geometry.circular_aperture(
        aperture_radius_mm=2.5,
        outer_radius_mm=5.0,
        length_mm=0.1,
    ),
    placement=Placement.in_front_detector(
        distance_mm=1.0,
    ),
)
```

The opening has:

```text
radius   = 2.5 mm
diameter = 5.0 mm
```

while the complete mask has:

```text
outer radius = 5.0 mm
```

---

# Rectangular aperture mask

A rectangular opening can be created using:

```python
Geometry.rectangular_aperture(...)
```

Example:

```python
mask = Internal_mask(
    name="rectangular_mask",
    material=Material.geant4("G4_W"),
    geometry=Geometry.rectangular_aperture(
        aperture_width_mm=4.0,
        aperture_height_mm=3.0,
        outer_width_mm=8.0,
        outer_height_mm=8.0,
        length_mm=0.1,
    ),
    placement=Placement.in_front_detector(
        distance_mm=1.0,
    ),
)
```

This creates:

```text
outer size    = 8 × 8 mm
opening size  = 4 × 3 mm
length        = 0.1 mm
```

---

# Mask material

The material is specified in the same way as other physical components.

For example, tungsten:

```python
Material.geant4("G4_W")
```

or aluminium:

```python
Material.geant4("G4_Al")
```

can be used.

Custom materials can also be supplied using `Material.custom_mat()`.

---

# Adding a mask to the detector

An internal mask is attached using:

```python
detector.add_internal_mask(
    mask
)
```

However, the detector must already have a housing.

This order is correct:

```python
detector.add_housing(
    housing
)

detector.add_internal_mask(
    mask
)
```

This order is required because internal masks belong to the detector housing assembly.

---

# Complete example

Assume a detector and housing have already been created.

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

detector.add_housing(
    housing
)

detector.add_internal_mask(
    mask
)
```

The detector now contains:

```text
Detector
   │
   ├── Housing
   │
   └── Internal mask
   │       └── aperture
   │
   └── Active detector volume
```

---

# Multiple internal masks

More than one internal mask can be added.

For example:

```python
mask_1 = Internal_mask(
    name="aluminium_mask",
    material=Material.geant4("G4_Al"),
    geometry=Geometry.circular_aperture(
        aperture_radius_mm=3.0,
        outer_radius_mm=5.0,
        length_mm=0.05,
    ),
    placement=Placement.in_front_detector(
        distance_mm=0.5,
    ),
)

mask_2 = Internal_mask(
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

detector.add_internal_mask(mask_1)
detector.add_internal_mask(mask_2)
```

Each mask is stored as a separate component in the detector configuration.

---

# Geometry restrictions

Internal masks can use normal solid or aperture geometry such as:

```python
Geometry.circular(...)
Geometry.rectangular(...)
Geometry.circular_aperture(...)
Geometry.rectangular_aperture(...)
```

Detector housing geometry cannot be used for an internal mask.

For most XRF detector masks, an aperture geometry is the most useful because it defines an opening through which photons can reach the detector.
