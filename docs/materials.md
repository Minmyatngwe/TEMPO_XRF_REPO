# Materials

RoboAI XRF supports both Geant4 predefined materials and custom materials.

## Geant4 materials

Use `Material.geant4()` when the material already exists in the Geant4 material database.

Example:

```python
from roboaixrf import Material

iron = Material.geant4(
    "G4_Fe"
)

print(iron)
```

Here:

```text
G4_Fe
```

is the Geant4 material name for iron.

Another example:

```python
from roboaixrf import Material

silicon = Material.geant4(
    "G4_Si"
)
```

This is useful for creating a silicon detector material.

## Custom materials

Use `Material.custom_mat()` when you want to define your own material from multiple elements.

Example:

```python
from roboaixrf import Material, Composition

copper_tungsten = Material.custom_mat(
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

This material contains:

```text
40% Cu by mass
60% W by mass
```

The mass fractions must add up to:

```text
1.0
```

## Composition

`Composition` describes one element inside a custom material.

Example:

```python
from roboaixrf import Composition

copper = Composition(
    element="Cu",
    mass_fraction=0.7,
)
```

This means that copper contributes:

```text
70%
```

of the material mass.

A second component can be created separately:

```python
zinc = Composition(
    element="Zn",
    mass_fraction=0.3,
)
```

These components can then be used together:

```python
from roboaixrf import Material, Composition

brass = Material.custom_mat(
    material_name="Brass",
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
```

## Using a material in a sample

Materials are normally passed into another RoboAI XRF object.

For example:

```python
from roboaixrf import (
    Material,
    Geometry,
    Sample,
)

iron = Material.geant4(
    "G4_Fe"
)

geometry = Geometry.rectangular(
    width_mm=10.0,
    height_mm=10.0,
    thickness_mm=1.0,
)

sample = Sample(
    name="iron_sample",
    material=iron,
    geometry=geometry,
)
```

The material and geometry are created separately and then combined inside the sample.
