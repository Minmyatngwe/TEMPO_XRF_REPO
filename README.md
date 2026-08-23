# TEMPO XRF Prototype

This repository is currently an internal development prototype for testing our custom XRF simulation workflow with Geant4.

It is **not yet a complete or production-ready package**. The main purpose of the repository is to test:

- Geant4 geometry construction
- XRF physics
- custom directional biasing / directional splitting
- X-ray source and beam generation
- detector geometry
- detector-response post-processing
- browser-based geometry/trajectory debugging
- communication between the Streamlit frontend and Geant4 backend

# AI Server / Ubuntu 24.04 Quick Start

If you are using the AI server with an Ubuntu 24.04 container for testing or development, you do not need to manually install all dependencies one by one.

From the directory containing `setup.sh`, run:

```bash
chmod +x setup.sh
./setup.sh
```

`setup.sh` is intended to prepare the current development environment automatically. It installs the required system packages, Node.js/npm, Python dependencies, builds and installs the patched Geant4 11.4.2 source, builds the TEMPO XRF backend, installs the Three.js/Vite viewer dependencies, and starts the Streamlit frontend.

For normal testing and development on the AI server, **running `setup.sh` is the recommended setup method**.

The manual installation sections below are mainly for understanding the setup, rebuilding individual components, or troubleshooting.

# Before Running Streamlit

Before starting the Streamlit frontend, make sure the following parts are prepared.

If `setup.sh` completed successfully on the Ubuntu 24.04 AI-server/container environment, these steps should already be handled.

## 1. Geant4

Geant4 must already be installed and usable from the terminal.

Source the Geant4 environment before building or running the simulation.

Example:

```bash
source /path/to/geant4-install/bin/geant4.sh
```

Check that Geant4 is available:

```bash
geant4-config --version
```

## 2. Required Geant4 Source Modification

Directional splitting currently requires a small modification to the Geant4 source code.

The provided `setup.sh` applies this modification automatically using:

```bash
python3 ./TEMPO_XRF_REPO/python_code/script.py geant4-v11.4.2
```

For manual installation, locate:

```cpp
G4EmBiasingManager::ApplyDirectionalSplitting
```

Inside this function there is a loop similar to:

```cpp
for (std::size_t kk = 0; kk < tmpSecondaries.size(); ++kk) {

    if (tmpSecondaries[kk]->GetParticleDefinition() == theGamma) {
        ...
    }
}
```

Add a null-pointer check before accessing `tmpSecondaries[kk]`:

```cpp
for (std::size_t kk = 0; kk < tmpSecondaries.size(); ++kk) {

    if (tmpSecondaries[kk] == nullptr) {
        continue;
    }

    if (tmpSecondaries[kk]->GetParticleDefinition() == theGamma) {
        ...
    }
}
```

Without this check, directional splitting may encounter a null secondary pointer and crash the simulation.

After modifying the Geant4 source, rebuild and reinstall Geant4 before building this project.

## 3. Build the Geant4 Backend

From the repository root:

```bash
mkdir -p build
cd build
cmake ..
cmake --build . -j$(nproc)
```

The simulation executable should then exist as:

```text
build/sim
```

Verify it exists:

```bash
ls build/sim
```

If C++ source files are changed later, rebuild with:

```bash
cd build
cmake --build . -j$(nproc)
```

## 4. Python Environment

The current setup script creates the virtual environment in the repository root:

```text
.venv/
```

For manual setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirement.txt
```

Make sure the virtual environment is active before starting Streamlit.

## 5. Browser 3D Viewer

The geometry/debug viewer uses:

- Vite
- Three.js
- CSS2DRenderer
- OrbitControls

Node.js and npm therefore need to be installed.

Check:

```bash
node --version
npm --version
npx --version
```

Install the viewer dependencies:

```bash
cd python_code/vis
npm ci
```

`node_modules/` is not stored in Git and must be generated locally.

The following files should remain in Git:

```text
package.json
package-lock.json
```

They define the JavaScript dependencies required by the viewer.

If the dependency files are being prepared for the first time:

```bash
npm install three
npm install --save-dev vite@5
```

After `package.json` and `package-lock.json` are committed, fresh installations should normally use only:

```bash
npm ci
```

## 6. Expected Project Structure

Before running the frontend, the important parts should approximately look like:

```text
TEMPO_XRF_REPO/
├── build/
│   └── sim
│
├── include/
├── src/
│
├── .venv/
│
├── python_code/
│   ├── frontend/
│   │   └── main.py
│   │
│   ├── vis/
│   │   ├── index.html
│   │   ├── main.js
│   │   ├── style.css
│   │   ├── package.json
│   │   ├── package-lock.json
│   │   └── public/
│   │
│   └── root_output_file/
│
├── CMakeLists.txt
├── requirement.txt
├── setup.sh
└── README.md
```

Generated folders such as:

```text
build/
.venv/
python_code/vis/node_modules/
python_code/vis/.vite/
```

are intentionally ignored by Git and must be created locally.

# Running Streamlit

On the Ubuntu 24.04 AI server, the recommended method is:

```bash
./setup.sh
```

For manual startup after installation:

```bash
source .venv/bin/activate
cd python_code/frontend
streamlit run main.py
```

The Streamlit frontend communicates with the compiled Geant4 executable in:

```text
build/sim
```

Do not start Streamlit before the Geant4 executable has been successfully built.

# Frontend Status

The frontend is currently a prototype and has not yet been thoroughly cleaned up or optimized.

A significant part of the frontend was initially generated with AI assistance and should therefore still be treated as development code.

It is currently sufficient for testing:

- the Geant4 backend
- simulation configuration
- geometry creation
- detector configuration
- simulation execution
- detector-response processing
- browser visualization/debugging

The frontend will be refactored and optimized later.

# Current Geometry Features

The user can currently configure several parts of the XRF system, including:

- X-ray tube
- X-ray tube filters
- sample
- detector
- detector housing
- detector collimators
- detector internal masks

Supported components can be positioned within the 3D Geant4 simulation world.

# Component Orientation

For supported components, the user can either:

- provide a custom rotation, or
- use automatic `face_sample` orientation.

When `face_sample` is selected, the backend calculates the rotation required for the component's local `+Z` axis to point toward the sample reference point.

The current sample reference point is:

```text
(0, 0, 0)
```

# X-ray Focal Spot and Beam

The focal-spot plane is constructed perpendicular to the vector between the sample reference point and the focal-spot center.

Primary photon positions are randomly sampled across the configured focal spot.

For each primary photon, a random target point is generated inside the calculated circular beam area on the sample.

The primary photon direction is then calculated from:

```text
source position
      ↓
random point inside sample beam area
```

The sample beam size is calculated from the source-to-collimator and collimator-to-sample geometry.

A virtual tube collimator is used for this calculation. This allows the source generator to directly produce photons with the expected beam divergence without requiring every primary photon to physically travel through a small tube collimator aperture.

# Browser Geometry / Debug Viewer

The project contains a Three.js browser viewer for debugging the Geant4 geometry.

The viewer can currently display:

- exported Geant4 geometry
- wireframe geometry
- surface geometry
- XYZ axes
- primary/particle trajectories
- beam directions
- Geant4 debug output

Runtime geometry calculations can be printed using `G4cout`, including values such as:

- calculated beam diameter
- calculated beam area
- source position
- source direction
- detector position
- component positions
- internal-mask positions
- material information
- geometry-placement calculations

These messages can be shown in the scrollable Debug Log panel while viewing the 3D geometry.

The browser viewer is intended primarily as a development/debugging tool at this stage.

# Detector Response / Noise

Detector response is processed separately from Geant4 particle transport.

This allows detector-response parameters to be modified without rerunning the full Geant4 transport simulation.

Examples include:

- energy resolution / FWHM
- detector gain
- zero offset
- Fano factor
- electron-hole pair creation energy
- MCA channel count
- live time
- pile-up parameters

This separation is useful because Geant4 transport can be computationally expensive, while detector-response processing can be repeated using the existing simulation result.

# Simulation Output

Simulation runs create run-specific output under the frontend run directory.

Typical development outputs include files such as:

```text
config.json
updated_config.json
*.root
xrf_geometry_vis.json
xrf_tracks.json
geant4_debug.log
```

## config.json

Contains the original simulation configuration provided to the backend.

## updated_config.json

Contains configuration and geometry information updated or calculated by the backend during geometry construction.

## ROOT (*.root)

Contains Geant4 simulation/scoring data used for later analysis and detector-response processing.

## Browser debug files

Files such as:

```text
xrf_geometry_vis.json
xrf_tracks.json
geant4_debug.log
```

are development/debug outputs used by the Three.js geometry and trajectory viewer.

# Current Status

This repository should currently be treated as:

```text
DEVELOPMENT / TESTING PROTOTYPE
```

and not as a production-ready XRF simulation package.

The current goal is to validate the complete workflow:

```text
Streamlit configuration
        ↓
JSON simulation configuration
        ↓
Geant4 geometry construction
        ↓
X-ray source generation
        ↓
XRF physics + biasing
        ↓
detector scoring
        ↓
simulation output
        ↓
detector-response processing
        ↓
analysis / visualization
```

Installation, frontend structure, error handling, performance optimization, and documentation will be improved as the project matures.
