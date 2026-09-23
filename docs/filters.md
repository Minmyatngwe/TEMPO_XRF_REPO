# Filters

RoboAI XRF supports two types of X-ray tube filtration:

1. **SpekPy filters**
2. **Physical Geant4 filters**

These filters are used differently.

---

# SpekPy filters

A SpekPy filter modifies the X-ray tube spectrum **before the photons are sent to Geant4**.

For example, an aluminium filter can be added to an X-ray tube with:

```python
tube.add_filter_spekpy(
    {
        "element": "Al",
        "thickness_mm": 0.5,
    }
)
```

This means:

```text
material  = Al
thickness = 0.5 mm
```

The filter is applied when the tube spectrum is generated.

## Adding multiple SpekPy filters

More than one filter can be added.

```python
tube.add_filter_spekpy(
    {
        "element": "Al",
        "thickness_mm": 0.5,
    }
)

tube.add_filter_spekpy(
    {
        "element": "Cu",
        "thickness_mm": 0.1,
    }
)
```

The filters are stored in the X-ray tube configuration.

---

# Physical Geant4 filters

A Geant4 filter is different.

It is a **real physical object in the simulation geometry**.

A Geant4 filter requires:

* a name
* a material
* a geometry
* a placement

Import the required classes with:

```python
from roboaixrf import (
    Filter,
    Material,
    Geometry,
    Placement,
)
```

## Creating a physical filter

For example:

```python
from roboaixrf import (
    Filter,
    Material,
    Geometry,
    Placement,
)

aluminium_filter = Filter(
    name="aluminium_filter",
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

This creates a physical aluminium disk with:

```text
radius     = 5 mm
thickness  = 0.5 mm
```

positioned:

```text
5 mm in front of the X-ray tube window
```

---

# Adding the physical filter to the X-ray tube

After creating the filter, add it to the tube with:

```python
tube.add_filter_geant4(
    aluminium_filter
)
```

A tube Geant4 filter must use:

```python
Placement.in_front_of_tube_window(...)
```

because the filter position must be referenced to the X-ray tube window.

For example:

```python
placement=Placement.in_front_of_tube_window(
    distance_mm=5.0,
)
```

---

# Rectangular physical filter

A physical filter does not have to be circular.

For example:

```python
from roboaixrf import (
    Filter,
    Material,
    Geometry,
    Placement,
)

copper_filter = Filter(
    name="copper_filter",
    material=Material.geant4("G4_Cu"),
    geometry=Geometry.rectangular(
        width_mm=10.0,
        height_mm=10.0,
        thickness_mm=0.1,
    ),
    placement=Placement.in_front_of_tube_window(
        distance_mm=3.0,
    ),
)
```

Then add it to the tube:

```python
tube.add_filter_geant4(
    copper_filter
)
```

---

# Complete tube filter example

Assume an X-ray tube has already been created:

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
```

A SpekPy filter can be added with:

```python
tube.add_filter_spekpy(
    {
        "element": "Al",
        "thickness_mm": 0.5,
    }
)
```

A physical Geant4 filter can be added separately:

```python
from roboaixrf import (
    Filter,
    Material,
    Geometry,
    Placement,
)

physical_filter = Filter(
    name="physical_al_filter",
    material=Material.geant4("G4_Al"),
    geometry=Geometry.circular(
        radius_mm=5.0,
        thickness_mm=0.5,
    ),
    placement=Placement.in_front_of_tube_window(
        distance_mm=5.0,
    ),
)

tube.add_filter_geant4(
    physical_filter
)
```

These two filters do **not** represent the same simulation method.

---

# SpekPy filter vs Geant4 filter

A SpekPy filter:

```python
tube.add_filter_spekpy(
    {
        "element": "Al",
        "thickness_mm": 0.5,
    }
)
```

modifies the generated source spectrum.

It does not create a physical filter object in the Geant4 geometry.

A Geant4 filter:

```python
tube.add_filter_geant4(
    physical_filter
)
```

creates a physical component that photons travel through during the Geant4 simulation.

---

# Which one should I use?

Use a **SpekPy filter** when you want filtration to be included directly in the generated tube spectrum.

Use a **Geant4 filter** when you want the filter to exist physically in the simulated geometry and interact with photons during transport.

Both methods can also be used in the same tube configuration when that matches the physical system being modelled.
