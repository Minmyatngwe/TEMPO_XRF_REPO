# RoboAI XRF

RoboAI XRF is a Python package for configuring and running X-ray fluorescence (XRF) simulations using Geant4.

The package provides Python classes for defining:

* materials
* sample geometry
* X-ray tube parameters
* detector geometry and placement
* filters and collimators
* detector housing and internal masks
* physics settings
* Geant4 simulation runs
* detector response and noise processing

## Installation

```bash
pip install roboaixrf
```

## Basic import

The main package components can be imported directly from `roboaixrf`:

```python
from roboaixrf import (
    XRFConfigure,
    Material,
    Composition,
    Geometry,
    Placement,
    Position,
    Orientation,
    Sample,
    XRayTube,
    TubePlacement,
    TubeWindow,
    Filter,
    Detector,
    Collimator,
    Housing,
    Internal_mask,
    Physics,
    RoboAiXrfSimulation,
)
```

## Documentation

The documentation will cover the package step by step:

1. Materials
2. Geometry
3. Placement and orientation
4. Samples
5. X-ray tubes
6. Filters
7. Detectors
8. Collimators
9. Detector housing
10. Physics configuration
11. Building an XRF configuration
12. Running a Geant4 simulation
13. Detector response and noise
14. Complete examples

## Simple example

A Geant4 material can be created with:

```python
from roboaixrf import Material

iron = Material.geant4("G4_Fe")

print(iron)
```

A geometry can be created separately:

```python
from roboaixrf import Geometry

sample_geometry = Geometry.rectangular(
    width_mm=10.0,
    height_mm=10.0,
    thickness_mm=1.0,
)
```

These objects can then be combined with other RoboAI XRF components to construct a complete simulation.
