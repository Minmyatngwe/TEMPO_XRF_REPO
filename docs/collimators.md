# Collimators

`Collimator` represents a physical collimator used to restrict the X-ray beam.

A collimator requires:

* a name
* a material
* an aperture geometry
* a placement

Import the required classes with:

```python
from roboaixrf import (
    Collimator,
    Material,
    Geometry,
    Placement,
)
```

---

# Circular collimator

Use `Geometry.circular_aperture()` for a collimator with a circular opening.

```python
from roboaixrf import (
    Collimator,
    Material,
    Geometry,
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

This creates a tungsten collimator with:

```text
aperture radius = 2 mm
outer radius    = 5 mm
length          = 1 mm
```

The central circular opening allows photons to pass through.

---

# Circular aperture parameters

`aperture_radius_mm`

Defines the radius of the open hole.

```python
aperture_radius_mm=2.0
```

means:

```text
opening radius = 2 mm
opening diameter = 4 mm
```

`outer_radius_mm`

Defines the outer radius of the complete collimator.

```python
outer_radius_mm=5.0
```

`length_mm`

Defines the length of the collimator along the beam direction.

```python
length_mm=1.0
```

---

# Rectangular collimator

Use `Geometry.rectangular_aperture()` for a rectangular opening.

```python
from roboaixrf import (
    Collimator,
    Material,
    Geometry,
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

This creates:

```text
Outer size:
    8 × 6 mm

Opening:
    3 × 2 mm

Length:
    1 mm
```

---

# Rectangular aperture parameters

The opening is controlled by:

```python
aperture_width_mm
aperture_height_mm
```

The complete outer body is controlled by:

```python
outer_width_mm
outer_height_mm
```

The thickness along the beam direction is controlled by:

```python
length_mm
```

For example:

```python
geometry = Geometry.rectangular_aperture(
    aperture_width_mm=4.0,
    aperture_height_mm=3.0,
    outer_width_mm=10.0,
    outer_height_mm=8.0,
    length_mm=2.0,
)
```

means:

```text
outer body = 10 × 8 mm
opening    = 4 × 3 mm
length     = 2 mm
```

---

# Collimator material

The collimator material determines how photons interact with the material surrounding the opening.

For example, tungsten can be used with:

```python
Material.geant4("G4_W")
```

Example:

```python
tungsten = Material.geant4("G4_W")

collimator = Collimator(
    name="tungsten_collimator",
    material=tungsten,
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

Custom materials can also be used.

```python
from roboaixrf import Material, Composition

custom_material = Material.custom_mat(
    material_name="CuW",
    density_g_cm3=12.0,
    compositions=[
        Composition(
            element="Cu",
            mass_fraction=0.4,
        ),
        Composition(
            element="W",
            mass_fraction=0.6,
        ),
    ],
)
```

The custom material can then be passed to the collimator:

```python
collimator = Collimator(
    name="custom_collimator",
    material=custom_material,
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

# Detector collimator placement

A collimator attached to a detector should use:

```python
Placement.in_front_detector(...)
```

For example:

```python
placement = Placement.in_front_detector(
    distance_mm=5.0,
)
```

This means that the collimator is positioned relative to the detector.

---

# Adding a collimator to a detector

After creating the collimator, attach it to the detector using:

```python
detector.add_collimator(
    collimator
)
```

Example:

```python
from roboaixrf import (
    Detector,
    Collimator,
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

detector.add_collimator(
    collimator
)
```

`Detector.add_collimator()` requires the collimator placement to reference the detector.

---

# Validating collimator geometry

`Collimator` provides:

```python
validate_collimator_geometry()
```

to check that an aperture geometry is being used.

Example:

```python
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

collimator.validate_collimator_geometry()
```

Valid collimator geometries are:

```python
Geometry.circular_aperture(...)
```

and:

```python
Geometry.rectangular_aperture(...)
```

A normal solid geometry such as:

```python
Geometry.circular(...)
```

should not be used for a collimator because it does not contain an opening.

---

# Complete example

```python
from roboaixrf import (
    Detector,
    Collimator,
    Material,
    Geometry,
    Placement,
)

# Detector
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

# Collimator
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

# Validate the aperture geometry
collimator.validate_collimator_geometry()

# Attach it to the detector
detector.add_collimator(
    collimator
)
```
