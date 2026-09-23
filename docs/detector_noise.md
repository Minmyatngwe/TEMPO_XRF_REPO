# Detector Response and Noise

`detector_noise()` converts the raw Geant4 detector response into a more realistic simulated detector spectrum.

The method performs three main steps:

1. Scale the Geant4 response to a physical X-ray tube exposure.
2. Apply detector effects such as energy broadening and pile-up.
3. Generate the final MCA spectrum.

The method belongs to `RoboAiXrfSimulation`:

```python
simulation.detector_noise(...)
```

---

# Required simulation workflow

Before using detector noise, the simulation must first be compiled and run.

```python
simulation.compile()

simulation.run(
    beam_on=1_000_000,
    number_of_thread=8,
)
```

Then detector response processing can be applied:

```python
results = simulation.detector_noise(
    fwhm=0.14,
    fwhm_energy_kev=5.9,
    detector_zero_offset=0.0,
    detector_gain_kev=0.025,
    live_time=30.0,
    pile_up_window_us=0.1,
)
```

The required order is:

```text
compile()
    ↓
run()
    ↓
simulation.root
    ↓
detector_noise()
    ↓
final detector spectrum
```

---

# Basic example

```python
final_count, energy, scaled_count, avg_yield, se_yield, spectrum_yield, spectrum_se = (
    simulation.detector_noise(
        fwhm=0.14,
        fwhm_energy_kev=5.9,
        detector_zero_offset=0.0,
        detector_gain_kev=0.025,
        live_time=30.0,
        pile_up_window_us=0.1,
    )
)
```

In this example:

```text
FWHM                  = 0.14 keV
reference energy      = 5.9 keV
zero offset           = 0 keV
gain                  = 0.025 keV/channel
live time             = 30 s
pile-up window        = 0.1 µs
```

---

# `fwhm`

`fwhm` defines the detector energy resolution at a reference energy.

For example:

```python
fwhm=0.14
```

means:

```text
FWHM = 0.14 keV
     = 140 eV
```

A smaller FWHM produces narrower spectral peaks.

A larger FWHM produces broader spectral peaks.

---

# `fwhm_energy_kev`

`fwhm_energy_kev` defines the energy at which the supplied FWHM value is specified.

For example:

```python
fwhm_energy_kev=5.9
```

together with:

```python
fwhm=0.14
```

means:

```text
Detector resolution = 140 eV FWHM at 5.9 keV
```

This is a common way of specifying the energy resolution of an X-ray detector.

---

# Detector gain

`detector_gain_kev` defines the energy represented by one MCA channel.

For example:

```python
detector_gain_kev=0.025
```

means:

```text
1 channel = 0.025 keV
          = 25 eV
```

The relationship between channel number and energy is approximately:

```text
Energy = zero offset + channel × gain
```

For example, with:

```text
gain = 0.025 keV/channel
channel = 200
zero offset = 0
```

the corresponding energy is:

```text
200 × 0.025 = 5.0 keV
```

---

# Detector zero offset

`detector_zero_offset` defines the energy offset of the MCA calibration.

For example:

```python
detector_zero_offset=0.0
```

means that channel zero corresponds to approximately:

```text
0 keV
```

With a non-zero offset:

```python
detector_zero_offset=0.1
```

the calibration becomes approximately:

```text
Energy = 0.1 + channel × gain
```

---

# Live time

`live_time` defines the physical acquisition time in seconds.

For example:

```python
live_time=30.0
```

means:

```text
30 second acquisition
```

Live time affects the number of physical photons expected during the measurement.

A longer acquisition normally produces more counts.

---

# Tube current

The tube current can optionally be supplied with:

```python
current=1.0
```

The unit is milliamperes.

For example:

```python
simulation.detector_noise(
    fwhm=0.14,
    fwhm_energy_kev=5.9,
    detector_zero_offset=0.0,
    detector_gain_kev=0.025,
    live_time=30.0,
    pile_up_window_us=0.1,
    current=1.0,
)
```

means:

```text
tube current = 1.0 mA
live time    = 30 s
```

The exposure is calculated as:

```text
mAs = current × live time
```

Therefore:

```text
1.0 mA × 30 s = 30 mAs
```

If `current` is not provided:

```python
current=None
```

the current stored in the X-ray tube configuration is used automatically.

For example, if the tube was created with:

```python
current_ma=0.5
```

then:

```python
simulation.detector_noise(
    ...
    current=None,
)
```

uses:

```text
0.5 mA
```

---

# Physical photon scaling

The number of Geant4 events is not the same as the physical number of photons produced during a real acquisition.

For example:

```python
simulation.run(
    beam_on=1_000_000,
    number_of_thread=8,
)
```

means Geant4 simulated:

```text
1,000,000 primary events
```

This does not mean that the real X-ray tube only produced one million photons.

During `detector_noise()`, RoboAI XRF calculates:

```text
mAs = current × live time
```

and calls SpekPy again using that physical exposure.

SpekPy provides the photon fluence at the virtual tube collimator.

The package then calculates the collimator area:

```text
A = πr²
```

and determines the physical number of photons:

```text
physical photons =
    fluence [photons/cm²]
    ×
    collimator area [cm²]
```

The Geant4 detector response is then scaled to this physical photon number.

---

# Last exposure information

After `detector_noise()` has been called, the last calculated exposure can be accessed with:

```python
simulation.last_mas
```

Example:

```python
print(simulation.last_mas)
```

For:

```text
current = 1 mA
live time = 30 s
```

the value is:

```text
30.0
```

The calculated physical number of incident photons can also be accessed with:

```python
simulation.last_incident_photons
```

Example:

```python
print(
    simulation.last_incident_photons
)
```

---

# Pile-up window

`pile_up_window_us` defines the detector pile-up time window in microseconds.

For example:

```python
pile_up_window_us=0.1
```

means:

```text
pile-up window = 0.1 µs
```

If photons arrive sufficiently close together in time, their detector signals can overlap.

This produces pile-up events in the simulated spectrum.

---

# Fano factor

The Fano factor controls statistical fluctuations in the number of charge carriers generated in the detector.

The default is:

```python
fano_factor=0.115
```

Normally this parameter does not need to be supplied unless a different detector model is required.

Example:

```python
simulation.detector_noise(
    fwhm=0.14,
    fwhm_energy_kev=5.9,
    detector_zero_offset=0.0,
    detector_gain_kev=0.025,
    live_time=30.0,
    pile_up_window_us=0.1,
    fano_factor=0.115,
)
```

---

# Electron-hole pair creation energy

The parameter:

```python
pair_creation_energy_ev
```

defines the average energy required to create one electron-hole pair in the detector.

The default is:

```python
pair_creation_energy_ev=3.6
```

The unit is electronvolts.

For a silicon detector, this means approximately:

```text
3.6 eV per electron-hole pair
```

---

# MCA channels

`mca_channels` defines the number of channels in the simulated multichannel analyzer.

The default is:

```python
mca_channels=2048
```

For example, with:

```text
2048 channels
gain = 0.025 keV/channel
```

the approximate energy range is:

```text
2048 × 0.025
=
51.2 keV
```

before considering the zero offset.

Example:

```python
simulation.detector_noise(
    fwhm=0.14,
    fwhm_energy_kev=5.9,
    detector_zero_offset=0.0,
    detector_gain_kev=0.025,
    live_time=30.0,
    pile_up_window_us=0.1,
    mca_channels=2048,
)
```

---

# Processing parameters

Two additional parameters control internal processing:

```python
chunk_size
number_of_buckets
```

Their defaults are:

```python
chunk_size=3_000_000
number_of_buckets=65
```

For normal use, these values can usually be left at their defaults.

They mainly control how the detector-noise calculation is processed internally rather than the physical detector configuration.

---

# Complete detector response example

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
    current=1.0,
    fano_factor=0.115,
    pair_creation_energy_ev=3.6,
    mca_channels=2048,
)
```

---

# Returned values

`detector_noise()` returns seven values.

## `final_count`

```python
final_count
```

contains the final counts after detector response and noise have been applied.

This is the final simulated detector spectrum.

---

## `energy`

```python
energy
```

contains the corresponding energy-bin centers in keV.

The final spectrum can therefore be plotted with:

```python
import matplotlib.pyplot as plt

plt.plot(
    energy,
    final_count,
)

plt.xlabel("Energy (keV)")
plt.ylabel("Counts")
plt.show()
```

---

## `scaled_count`

```python
scaled_count
```

contains the physically scaled Geant4 spectrum before detector noise is applied.

This is useful for comparing:

```text
ideal scaled Geant4 response
            ↓
detector response model
            ↓
final detector spectrum
```

---

## `average_channel_wise_yield`

```python
average_channel_wise_yield
```

contains the average detector yield calculated for each MCA channel.

---

## `se_channel_wise_yield`

```python
se_channel_wise_yield
```

contains the standard error associated with the channel-wise yield.

---

## `spectrum_yield_avg`

```python
spectrum_yield_avg
```

contains the average total spectrum yield calculated from the Geant4 response.

---

## `spectrum_se`

```python
spectrum_se
```

contains the standard error associated with the total spectrum yield.

---

# Generated spectrum plot

`detector_noise()` automatically creates an interactive HTML spectrum file:

```text
simulation_spectrum.html
```

inside the simulation run directory.

For example:

```text
runs/
└── iron_sample/
    ├── config.json
    ├── run.mac
    ├── simulation.root
    └── simulation_spectrum.html
```

The HTML output contains two plots:

```text
Before Detector Noise
```

and:

```text
After Detector Noise
```

This makes it possible to compare the physically scaled Geant4 spectrum with the final simulated detector response.

---

# Full workflow

A complete simulation and detector-response workflow looks like:

```python
from pathlib import Path

from roboaixrf import RoboAiXrfSimulation

simulation = RoboAiXrfSimulation(
    config=config,
    config_path=Path("runs/iron_sample"),
)

# Prepare the source and configuration
simulation.compile()

# Run Geant4
simulation.run(
    beam_on=1_000_000,
    number_of_thread=8,
)

# Apply physical scaling and detector response
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
    current=1.0,
)

print(
    "Exposure:",
    simulation.last_mas,
    "mAs",
)

print(
    "Incident photons:",
    simulation.last_incident_photons,
)
```

The resulting workflow is:

```text
XRF configuration
       ↓
compile()
       ↓
SpekPy source spectrum
       ↓
run()
       ↓
Geant4 detector response
       ↓
physical current/time scaling
       ↓
detector noise and pile-up
       ↓
final MCA spectrum
```
