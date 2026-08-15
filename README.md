TEMPO_XRF_REPO

This repository is not complete. It is currently intended only for testing how Geant4 works with our custom XRF simulation algorithms.

Because this is currently an internal prototype for team testing, full installation instructions are not provided yet.

Important: Geant4 Source Modification

Before running the simulation with directional biasing / directional splitting, a small modification to the Geant4 source code is currently required.

Find your installed Geant4 source code and locate:

G4EmBiasingManager::ApplyDirectionalSplitting

Inside this function, you should find code similar to:

for (std::size_t kk = 0; kk < tmpSecondaries.size(); ++kk) {

    if (tmpSecondaries[kk]->GetParticleDefinition() == theGamma) {
        ...
    }
}

Before accessing tmpSecondaries[kk], add a null-pointer check:

if (tmpSecondaries[kk] == nullptr) {
    continue;
}

For example:

for (std::size_t kk = 0; kk < tmpSecondaries.size(); ++kk) {

    if (tmpSecondaries[kk] == nullptr) {
        continue;
    }

    if (tmpSecondaries[kk]->GetParticleDefinition() == theGamma) {
        ...
    }
}

Without this check, directional biasing can encounter a null secondary pointer and cause the simulation to crash.

After modifying the Geant4 source, Geant4 must be rebuilt before using the modified implementation.

Frontend

The frontend is currently a prototype and was largely generated with AI assistance. It has not yet been thoroughly reviewed or optimized.

It is currently good enough for testing the Geant4 backend and the overall simulation workflow.

The frontend will be cleaned up and optimized later.

Current Features

The user can currently configure several parts of the XRF geometry, including:

detector housing

detector internal masks

detector collimators

X-ray tube filters

X-ray tube

sample

The tube, sample, detector, collimators, and other supported components can be positioned within the 3D simulation world.

Component Orientation

For supported components, the user can either provide a custom rotation or request that the backend automatically orient the component toward the sample.

When face_sample orientation is used, the backend calculates the required rotation so that the component's local +Z axis points toward the sample reference point, currently (0, 0, 0).

X-ray Focal Spot and Beam

The focal-spot plane is perpendicular to the vector between the sample reference point and the focal-spot center.

Primary photon positions are randomly sampled across the configured focal spot.

Photon directions are then sampled toward random positions inside the calculated beam area on the sample.

The beam area is calculated using a virtual tube collimator, allowing the simulation to model the expected beam footprint on the sample without explicitly transporting large numbers of photons through a physical tube collimator.

Detector Response / Noise

Detector noise is applied separately from the Geant4 transport simulation.

This means the user can change detector-response parameters and reprocess the simulation output without rerunning the full Geant4 simulation.

Simulation Output

After a simulation, the user can download the generated run data.

The output includes files such as:

config.json
updated.json
*.h5

config.json contains the original simulation configuration.

updated.json contains geometry/configuration information updated by the backend during simulation setup.

The HDF5 (.h5) file contains the simulation data used for later analysis and detector-response processing.

Current Status

This repository should currently be treated as a development/testing prototype, not a production-ready simulation package.

The main purpose at this stage is to validate:

Geant4 geometry

XRF physics

custom directional biasing

source/beam generation

detector geometry

detector-response post-processing

the interaction between the frontend and Geant4 backend
