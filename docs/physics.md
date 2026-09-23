# Physics

`Physics` controls the physics settings used by the XRF simulation.

It includes settings for:

* fluorescence
* Auger emission
* PIXE
* atomic de-excitation cuts
* fluorescence data
* interaction biasing
* secondary splitting
* production cuts

Import it with:

```python
from roboaixrf import Physics
```

---

# Basic physics configuration

The simplest way to create a physics configuration is:

```python
from roboaixrf import Physics

physics = Physics()
```

This uses the package default settings.

The current defaults are equivalent to:

```python
physics = Physics(
    interaction_bias_use=True,
    secondary_splitting_use=True,

    flu_use=True,
    auger_use=True,
    pixe_use=False,
    ignore_cut_use=True,

    flu_dataset_name="ANSTO",

    maximum_energy=1000,

    phot_factor=100,
    compt_factor=100,
    rayl_factor=100,

    electron_cut=0.01,
    gamma_cut=0.01,
    positron_cut=0.01,
    proton_cut=0.01,
)
```

---

# Fluorescence

Fluorescence can be enabled with:

```python
flu_use=True
```

For example:

```python
physics = Physics(
    flu_use=True,
)
```

When fluorescence is enabled, atomic vacancies can produce characteristic X-rays during atomic de-excitation.

For XRF simulations, this is normally required because the characteristic X-ray peaks are produced through fluorescence.

---

# Auger emission

Auger emission is controlled with:

```python
auger_use=True
```

Example:

```python
physics = Physics(
    flu_use=True,
    auger_use=True,
)
```

When Auger emission is enabled, an atomic vacancy can also relax by emitting an Auger electron instead of a fluorescence photon.

---

# PIXE

PIXE is controlled with:

```python
pixe_use=True
```

The default is:

```python
pixe_use=False
```

Example:

```python
physics = Physics(
    pixe_use=True,
)
```

PIXE stands for:

```text
Particle-Induced X-ray Emission
```

Enable it when particle-induced atomic ionization is required by the simulation.

---

# Ignore de-excitation cuts

Atomic de-excitation production cuts are controlled with:

```python
ignore_cut_use=True
```

The default is:

```python
True
```

Example:

```python
physics = Physics(
    ignore_cut_use=True,
)
```

This setting determines whether atomic de-excitation should ignore normal production cuts when generating secondary particles.

---

# Fluorescence dataset

The fluorescence dataset is selected using:

```python
flu_dataset_name
```

The current default is:

```python
flu_dataset_name="ANSTO"
```

Example:

```python
physics = Physics(
    flu_dataset_name="ANSTO",
)
```

This tells the simulation which fluorescence data source should be used by the RoboAI XRF atomic de-excitation configuration.

---

# Interaction biasing

Interaction biasing can be enabled with:

```python
interaction_bias_use=True
```

Example:

```python
physics = Physics(
    interaction_bias_use=True,
)
```

Interaction biasing is used to increase the probability that useful photon interactions occur in the sample.

This can improve simulation efficiency when the probability of an interaction is naturally low.

Disable it with:

```python
physics = Physics(
    interaction_bias_use=False,
)
```

---

# Secondary splitting

Secondary splitting is controlled with:

```python
secondary_splitting_use=True
```

Example:

```python
physics = Physics(
    secondary_splitting_use=True,
)
```

Secondary splitting is a variance-reduction technique used to generate additional statistically weighted secondary particles from selected interactions.

The amount of splitting is controlled using separate factors.

---

# Photoelectric factor

The photoelectric splitting factor is:

```python
phot_factor
```

The default is:

```python
phot_factor=100
```

Example:

```python
physics = Physics(
    secondary_splitting_use=True,
    phot_factor=100,
)
```

This factor controls the configured secondary splitting for photoelectric interactions.

---

# Compton factor

The Compton splitting factor is:

```python
compt_factor
```

The default is:

```python
compt_factor=100
```

Example:

```python
physics = Physics(
    secondary_splitting_use=True,
    compt_factor=100,
)
```

---

# Rayleigh factor

The Rayleigh splitting factor is:

```python
rayl_factor
```

The default is:

```python
rayl_factor=100
```

Example:

```python
physics = Physics(
    secondary_splitting_use=True,
    rayl_factor=100,
)
```

The three factors can be configured together:

```python
physics = Physics(
    secondary_splitting_use=True,
    phot_factor=100,
    compt_factor=100,
    rayl_factor=100,
)
```

---

# Maximum energy

The maximum energy used by the biasing configuration is controlled by:

```python
maximum_energy
```

The default is:

```python
maximum_energy=1000
```

Example:

```python
physics = Physics(
    maximum_energy=1000,
)
```

---

# Production cuts

Production cuts can be configured separately for:

```text
gamma
electron
positron
proton
```

The current defaults are:

```python
gamma_cut=0.01
electron_cut=0.01
positron_cut=0.01
proton_cut=0.01
```

Example:

```python
physics = Physics(
    gamma_cut=0.01,
    electron_cut=0.01,
    positron_cut=0.01,
    proton_cut=0.01,
)
```

These values are passed to the Geant4 physics configuration as production-cut settings.

---

# Configuration without biasing

Biasing can be disabled when a purely analogue simulation is required.

For example:

```python
from roboaixrf import Physics

physics = Physics(
    interaction_bias_use=False,
    secondary_splitting_use=False,
    flu_use=True,
    auger_use=True,
)
```

The atomic physics remains enabled while the variance-reduction methods are disabled.

---

# Example XRF physics configuration

A typical configuration can be written as:

```python
from roboaixrf import Physics

physics = Physics(
    interaction_bias_use=True,
    secondary_splitting_use=True,

    flu_use=True,
    auger_use=True,
    pixe_use=False,
    ignore_cut_use=True,

    flu_dataset_name="ANSTO",

    maximum_energy=1000,

    phot_factor=100,
    compt_factor=100,
    rayl_factor=100,

    gamma_cut=0.01,
    electron_cut=0.01,
    positron_cut=0.01,
    proton_cut=0.01,
)
```

This configuration enables atomic fluorescence and Auger de-excitation together with the package's interaction-biasing and secondary-splitting features.

The resulting `Physics` object can later be included in the complete `XRFConfigure` simulation configuration.
