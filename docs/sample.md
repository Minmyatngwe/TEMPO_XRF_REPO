# Sample

`Sample` defines the material and physical geometry of the sample being analyzed in the XRF simulation.

Import it with:

```python
from roboaixrf import Sample
```

A sample requires:

* a name
* a material
* a geometry

## Basic example

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
```

This creates an iron sample with the dimensions:

```text
width     = 10 mm
height    = 10 mm
thickness = 1 mm
```

---

## `name`

`name` identifies the sample inside the simulation.

```python
sample = Sample(
    name="steel_sample",
    material=Material.geant4("G4_Fe"),
    geometry=Geometry.rectangular(
        width_mm=10.0,
        height_mm=10.0,
        thickness_mm=1.0,
    ),
)
```

The name can be chosen by the user.

For example:

```text
iron_sample
steel_sample
reference_sample
sample_1
```

---

## `material`

The `material` parameter defines what the sample is made from.

For example, an iron sample can use:

```python
Material.geant4("G4_Fe")
```

A complete example is:

```python
from roboaixrf import (
    Sample,
    Material,
    Geometry,
)

iron = Material.geant4("G4_Fe")

sample = Sample(
    name="iron_sample",
    material=iron,
    geometry=Geometry.rectangular(
        width_mm=6.0,
        height_mm=6.0,
        thickness_mm=1.0,
    ),
)
```

Custom materials can also be used.

```python
from roboaixrf import (
    Sample,
    Material,
    Composition,
    Geometry,
)

alloy = Material.custom_mat(
    material_name="CuZn",
    density_g_cm3=8.5,
    compositions=[
        Composition(
            element="Cu",
            mass_fraction=0.7,
        ),
        Composition(
            element="Zn",
            mass_fraction=0.3,
        ),
    ],
)

sample = Sample(
    name="alloy_sample",
    material=alloy,
    geometry=Geometry.rectangular(
        width_mm=10.0,
        height_mm=10.0,
        thickness_mm=1.0,
    ),
)
```

---

# Sample geometry

Samples can currently use two geometry types:

```python
Geometry.rectangular(...)
```

or:

```python
Geometry.circular(...)
```

Other geometry types, such as aperture geometries, are not valid sample shapes.

## Rectangular sample

```python
from roboaixrf import (
    Sample,
    Material,
    Geometry,
)

sample = Sample(
    name="copper_sample",
    material=Material.geant4("G4_Cu"),
    geometry=Geometry.rectangular(
        width_mm=10.0,
        height_mm=8.0,
        thickness_mm=0.5,
    ),
)
```

This produces a sample with:

```text
width     = 10 mm
height    = 8 mm
thickness = 0.5 mm
```

---

## Circular sample

A circular sample can be created using `Geometry.circular()`.

```python
from roboaixrf import (
    Sample,
    Material,
    Geometry,
)

sample = Sample(
    name="circular_copper_sample",
    material=Material.geant4("G4_Cu"),
    geometry=Geometry.circular(
        radius_mm=5.0,
        thickness_mm=1.0,
    ),
)
```

This produces a sample with:

```text
radius    = 5 mm
diameter  = 10 mm
thickness = 1 mm
```

---

# Validation

`Sample` only accepts rectangular and circular geometries.

For example, this is valid:

```python
geometry = Geometry.rectangular(
    width_mm=10.0,
    height_mm=10.0,
    thickness_mm=1.0,
)
```

and this is valid:

```python
geometry = Geometry.circular(
    radius_mm=5.0,
    thickness_mm=1.0,
)
```

An aperture geometry should not be used as a sample geometry.

For example:

```python
Geometry.circular_aperture(...)
```

is intended for components such as collimators and masks, not samples.

---

# Complete simple example

```python
from roboaixrf import (
    Material,
    Geometry,
    Sample,
)

material = Material.geant4(
    "G4_Fe"
)

geometry = Geometry.rectangular(
    width_mm=6.0,
    height_mm=6.0,
    thickness_mm=1.0,
)

sample = Sample(
    name="iron_sample",
    material=material,
    geometry=geometry,
)

print(sample)
```

This creates a complete sample object that can later be added to an XRF simulation configuration.
