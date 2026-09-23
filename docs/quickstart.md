# Quick Start

This guide shows how to create and run a basic XRF simulation from start to finish.

In this example we will simulate:

* an iron sample
* a tungsten X-ray tube
* a silicon detector
* air surrounding the system

The complete workflow is:

```text
Create physics
      ↓
Create world
      ↓
Create sample
      ↓
Create detector
      ↓
Create X-ray tube
      ↓
Create tube window
      ↓
Build XRF configuration
      ↓
Create simulation
      ↓
compile()
      ↓
run()
      ↓
detector_noise()
```

---

# 1. Import RoboAI XRF

```python
from pathlib import Path

from roboaixrf import (
    XRFConfigure,
    Material,
    Geometry,
    Placement,
    Sample,
    Detector,
    XRayTube,
    TubePlacement,
    TubeWindow,
    Physics,
    RoboAiXrfSimulation,
)
```

---

# 2. Create the physics configuration

```python
physics = Physics(
    flu_use=True,
    auger_use=True,
    pixe_use=False,
    ignore_cut_use=True,
    flu_dataset_name="ANSTO",
)
```

This enables fluorescence and Auger atomic de-excitation.

---

# 3. Create the simulation world

Create an air-filled world:

```python
config = XRFConfigure(
    world_material=Material.geant4("G4_AIR"),
    world_size_x_mm=300.0,
    world_size_y_mm=300.0,
    world_size_z_mm=300.0,
    physics=physics,
)
```

The simulation world is:

```text
300 × 300 × 300 mm
```

and contains air.

---

# 4. Create the sample

Create an iron sample:

```python
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

The sample is:

```text
Material  = Fe
Width     = 10 mm
Height    = 10 mm
Thickness = 1 mm
```

Add it to the configuration:

```python
config.add(sample)
```

---

# 5. Create the detector

Create a circular silicon detector:

```python
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

This detector has:

```text
Material   = Si
Radius     = 4 mm
Thickness  = 1 mm

Distance   = 17 mm from sample
Elevation  = 90°
Azimuth    = 50°
```

Add it to the configuration:

```python
config.add(detector)
```

---

# 6. Define the X-ray tube position

The X-ray tube position is defined separately using `TubePlacement`.

```python
tube_placement = TubePlacement(
    focal_spot_to_sample_distance_mm=140.0,
    tube_window_to_sample_distance_mm=130.0,
    elevation_deg=90.0,
    azimuth_deg=0.0,
)
```

This gives:

```text
Focal spot → sample = 140 mm
Tube window → sample = 130 mm
```

---

# 7. Create the X-ray tube

Create a tungsten tube operating at 50 kV and 1 mA:

```python
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

The important tube parameters are:

```text
Target             = W
Voltage            = 50 kV
Current            = 1 mA
Anode angle        = 15°
Focal spot diameter = 0.05 mm
```

---

# 8. Create the tube window

Create a beryllium tube window:

```python
tube_window = TubeWindow(
    name="beryllium_window",
    material=Material.geant4("G4_Be"),
    thickness_mm=0.01,
)
```

Attach it to the tube:

```python
tube.set_window(tube_window)
```

Check that the tube has all required components:

```python
tube.validate_complete()
```

---

# 9. Add the tube to the configuration

```python
config.add(tube)
```

The configuration now contains:

```text
XRFConfigure
│
├── World
├── Physics
├── Sample
├── Detector
└── X-ray tube
    └── Tube window
```

Validate everything:

```python
config.validate_complete()
```

---

# 10. Create the simulation

Create a directory for this simulation run:

```python
simulation = RoboAiXrfSimulation(
    config=config,
    config_path=Path("runs/iron_example"),
)
```

The directory will contain the generated simulation files.

---

# 11. Compile the configuration

Prepare the X-ray source spectrum and Geant4 configuration:

```python
simulation.compile()
```

You can check the state with:

```python
print(simulation.is_compiled)
```

After compilation:

```text
True
```

should be returned.

A configuration file is also written to:

```text
runs/iron_example/config.json
```

---

# 12. Run Geant4

Run 100,000 primary events using four threads:

```python
simulation.run(
    beam_on=100_000,
    number_of_thread=4,
)
```

After a successful run:

```python
print(simulation.beam_on)
```

should show:

```text
100000
```

The Geant4 result is stored in:

```text
runs/iron_example/simulation.root
```

For a real quantitative simulation, a larger `beam_on` value may be required to obtain sufficient statistics.

---

# 13. Apply detector response

The raw Geant4 spectrum can now be converted into a more realistic detector spectrum.

```python
(
    final_count,
    energy,
    scaled_count,
    average_channel_wise_yield,
    se_channel_wise_yield,
    spectrum_yield_avg,
    spectrum_se,
) = simulation.detector_noise(
    fwhm=0.14,
    fwhm_energy_kev=5.9,
    detector_zero_offset=0.0,
    detector_gain_kev=0.025,
    live_time=30.0,
    pile_up_window_us=0.1,
)
```

Because `current` was not supplied, the tube current:

```text
1.0 mA
```

is used automatically.

The physical exposure is therefore:

```text
1.0 mA × 30 s
=
30 mAs
```

---

# 14. Plot the final spectrum

The returned `energy` and `final_count` arrays can be plotted directly.

```python
import matplotlib.pyplot as plt

plt.plot(
    energy,
    final_count,
)

plt.xlabel("Energy (keV)")
plt.ylabel("Counts")
plt.title("Simulated XRF Spectrum")

plt.show()
```

---

# Complete example

The entire example can be written as one Python script:

```python
from pathlib import Path

import matplotlib.pyplot as plt

from roboaixrf import (
    XRFConfigure,
    Material,
    Geometry,
    Placement,
    Sample,
    Detector,
    XRayTube,
    TubePlacement,
    TubeWindow,
    Physics,
    RoboAiXrfSimulation,
)


# Physics

physics = Physics(
    flu_use=True,
    auger_use=True,
    pixe_use=False,
    ignore_cut_use=True,
    flu_dataset_name="ANSTO",
)


# World

config = XRFConfigure(
    world_material=Material.geant4("G4_AIR"),
    world_size_x_mm=300.0,
    world_size_y_mm=300.0,
    world_size_z_mm=300.0,
    physics=physics,
)


# Sample

sample = Sample(
    name="iron_sample",
    material=Material.geant4("G4_Fe"),
    geometry=Geometry.rectangular(
        width_mm=10.0,
        height_mm=10.0,
        thickness_mm=1.0,
    ),
)

config.add(sample)


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

config.add(detector)


# X-ray tube placement

tube_placement = TubePlacement(
    focal_spot_to_sample_distance_mm=140.0,
    tube_window_to_sample_distance_mm=130.0,
    elevation_deg=90.0,
    azimuth_deg=0.0,
)


# X-ray tube

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


# Tube window

tube_window = TubeWindow(
    name="beryllium_window",
    material=Material.geant4("G4_Be"),
    thickness_mm=0.01,
)

tube.set_window(tube_window)
tube.validate_complete()

config.add(tube)


# Validate configuration

config.validate_complete()


# Create simulation

simulation = RoboAiXrfSimulation(
    config=config,
    config_path=Path("runs/iron_example"),
)


# Prepare source spectrum and configuration

simulation.compile()


# Run Geant4

simulation.run(
    beam_on=100_000,
    number_of_thread=4,
)


# Apply detector response

(
    final_count,
    energy,
    scaled_count,
    average_channel_wise_yield,
    se_channel_wise_yield,
    spectrum_yield_avg,
    spectrum_se,
) = simulation.detector_noise(
    fwhm=0.14,
    fwhm_energy_kev=5.9,
    detector_zero_offset=0.0,
    detector_gain_kev=0.025,
    live_time=30.0,
    pile_up_window_us=0.1,
)


# Plot final spectrum

plt.plot(
    energy,
    final_count,
)

plt.xlabel("Energy (keV)")
plt.ylabel("Counts")
plt.title("Simulated XRF Spectrum")

plt.show()
```

# What happens internally?

The full simulation pipeline is:

```text
Python configuration
        ↓
SpekPy
        ↓
X-ray tube spectrum
        ↓
Geant4
        ↓
Photon transport
        ↓
Sample interactions
        ↓
X-ray fluorescence
        ↓
Detector energy deposition
        ↓
simulation.root
        ↓
Physical exposure scaling
        ↓
Detector broadening + pile-up
        ↓
Final XRF spectrum
```

This is the basic workflow for using RoboAI XRF from Python.
