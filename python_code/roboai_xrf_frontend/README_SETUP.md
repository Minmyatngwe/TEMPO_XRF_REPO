# TEMPO_XRF_REPO — New Machine Setup

This guide sets up the `front` branch of TEMPO_XRF_REPO on a fresh Ubuntu 24.04 machine.

Recommended environment:

- Ubuntu 24.04
- Python 3.12
- GCC/G++ 13+
- CMake
- Geant4 11.4.2
- xraylib
- Node.js 22
- npm
- Streamlit
- SpekPy
- NumPy / Pandas / Plotly
- Uproot / Awkward
- Pydantic

---

# 1. Update Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
```

---

# 2. Install system packages

```bash
sudo apt install -y \
    git \
    git-lfs \
    curl \
    wget \
    ca-certificates \
    gnupg \
    software-properties-common \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    ninja-build \
    pkg-config \
    python3 \
    python3-dev \
    python3-venv \
    python3-pip \
    libexpat1-dev \
    zlib1g-dev \
    libxerces-c-dev \
    nlohmann-json3-dev \
    libx11-dev \
    libxmu-dev \
    libxi-dev \
    libxt-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    freeglut3-dev \
    mesa-common-dev \
    libcairo2-dev \
    libpango1.0-dev \
    ffmpeg
```

Enable Ubuntu Universe repository:

```bash
sudo add-apt-repository -y universe
sudo apt update
```

Install xraylib C/C++ development files:

```bash
sudo apt install -y libxrl-dev
```

Initialize Git LFS:

```bash
git lfs install
```

Check basic tools:

```bash
python3 --version
g++ --version
cmake --version
git --version
```

---

# 3. Install Node.js 22

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

Check:

```bash
node --version
npm --version
```

---

# 4. Install Geant4 11.4.2

Create directories:

```bash
mkdir -p ~/geant4
cd ~/geant4
```

Download Geant4:

```bash
wget https://github.com/Geant4/geant4/archive/refs/tags/v11.4.2.tar.gz \
    -O geant4-v11.4.2.tar.gz
```

Extract:

```bash
tar -xzf geant4-v11.4.2.tar.gz
```

Rename source directory:

```bash
mv geant4-11.4.2 geant4-v11.4.2
```

Create build and install directories:

```bash
mkdir -p ~/geant4/geant4-v11.4.2-build
mkdir -p ~/geant4/geant4-install
```

Configure Geant4:

```bash
cmake \
    -S ~/geant4/geant4-v11.4.2 \
    -B ~/geant4/geant4-v11.4.2-build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=$HOME/geant4/geant4-install \
    -DGEANT4_BUILD_MULTITHREADED=ON \
    -DGEANT4_INSTALL_DATA=ON \
    -DGEANT4_INSTALL_EXAMPLES=OFF \
    -DGEANT4_USE_GDML=ON \
    -DGEANT4_USE_SYSTEM_EXPAT=ON \
    -DGEANT4_USE_SYSTEM_XERCESC=ON \
    -DGEANT4_USE_OPENGL_X11=OFF \
    -DGEANT4_USE_QT=OFF
```

Build:

```bash
cmake --build ~/geant4/geant4-v11.4.2-build -j$(nproc)
```

Install:

```bash
cmake --install ~/geant4/geant4-v11.4.2-build
```

Load Geant4:

```bash
source ~/geant4/geant4-install/bin/geant4.sh
```

Check:

```bash
geant4-config --version
```

Expected:

```text
11.4.2
```

---

# 5. Automatically load Geant4 in every terminal

```bash
echo 'source $HOME/geant4/geant4-install/bin/geant4.sh' >> ~/.bashrc
```

Reload shell:

```bash
source ~/.bashrc
```

Check again:

```bash
geant4-config --version
```

---

# 6. Clone TEMPO_XRF_REPO

```bash
cd ~
```

Clone the `front` branch:

```bash
git clone --branch front --single-branch \
https://github.com/Minmyatngwe/TEMPO_XRF_REPO.git
```

Enter the repository:

```bash
cd ~/TEMPO_XRF_REPO
```

---

# 7. Create Python virtual environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Upgrade Python packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Check:

```bash
which python
python --version
pip --version
```

---

# 8. Install frontend Python requirements

If this file exists:

```text
python_code/roboai_xrf_frontend/requirements.txt
```

install it with:

```bash
python -m pip install \
    -r python_code/roboai_xrf_frontend/requirements.txt
```

---

# 9. Install XRF backend Python packages

```bash
python -m pip install \
    numpy \
    pandas \
    plotly \
    streamlit \
    pydantic \
    spekpy \
    uproot \
    awkward \
    xraylib
```

---

# 10. Optional: install exact pinned versions

If you want the environment to match the current working setup more closely:

```bash
python -m pip install \
    awkward==2.9.1 \
    numpy==2.4.6 \
    pandas==3.0.3 \
    plotly==6.9.0 \
    pydantic==2.13.4 \
    spekpy==2.5.4 \
    streamlit==1.58.0 \
    uproot==5.7.4
```

Then install Python xraylib:

```bash
python -m pip install xraylib
```

Do not run both the generic package install and pinned install unless you intentionally want the pinned versions to overwrite the generic versions.

---

# 11. Install local Python package

From:

```bash
cd ~/TEMPO_XRF_REPO
```

If the repository contains `pyproject.toml`, `setup.py`, or `setup.cfg`, run:

```bash
python -m pip install -e .
```

Check:

```bash
python -c "import roboaixrf; print(roboaixrf.__file__)"
```

---

# 12. Install visualization frontend dependencies

Go to the visualization directory:

```bash
cd ~/TEMPO_XRF_REPO/roboaixrf/vis
```

If `package-lock.json` exists:

```bash
npm ci
```

Otherwise:

```bash
npm install
```

If Three.js, Plotly.js, or Vite are missing:

```bash
npm install three plotly.js-dist-min
npm install --save-dev vite
```

Check:

```bash
npm list
```

---

# 13. Test Vite visualization

```bash
cd ~/TEMPO_XRF_REPO/roboaixrf/vis
```

Run:

```bash
npm run dev -- --host 0.0.0.0
```

or:

```bash
npx vite --host 0.0.0.0
```

Default Vite address is usually:

```text
http://localhost:5173
```

Stop it with:

```text
Ctrl+C
```

---

# 14. Build the Geant4 backend

First activate Geant4:

```bash
source ~/geant4/geant4-install/bin/geant4.sh
```

Activate Python environment:

```bash
cd ~/TEMPO_XRF_REPO
source .venv/bin/activate
```

If the Geant4 project is located here:

```text
~/TEMPO_XRF_REPO/geant4_code
```

run:

```bash
cd ~/TEMPO_XRF_REPO/geant4_code
```

Remove old build:

```bash
rm -rf build
```

Configure:

```bash
cmake \
    -S . \
    -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH=$HOME/geant4/geant4-install
```

Compile:

```bash
cmake --build build -j$(nproc)
```

---

# 15. If the Geant4 backend is inside roboaixrf

If instead the CMake project is located at:

```text
~/TEMPO_XRF_REPO/roboaixrf/geant4_code
```

use:

```bash
cd ~/TEMPO_XRF_REPO/roboaixrf/geant4_code
```

Then:

```bash
rm -rf build
```

```bash
cmake \
    -S . \
    -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH=$HOME/geant4/geant4-install
```

```bash
cmake --build build -j$(nproc)
```

---

# 16. Check xraylib C++ installation

```bash
find /usr/include -name "xraylib.h"
```

Expected:

```text
/usr/include/xraylib.h
```

Check shared library:

```bash
ldconfig -p | grep xrl
```

---

# 17. Check Python xraylib

Activate environment:

```bash
cd ~/TEMPO_XRF_REPO
source .venv/bin/activate
```

Run:

```bash
python -c "import xraylib; print('xraylib OK')"
```

---

# 18. Verify all Python packages

```bash
python - <<'PY'
import sys
import numpy
import pandas
import awkward
import uproot
import plotly
import pydantic
import spekpy
import streamlit
import xraylib

print("Python:    ", sys.version)
print("NumPy:     ", numpy.__version__)
print("Pandas:    ", pandas.__version__)
print("Awkward:   ", awkward.__version__)
print("Uproot:    ", uproot.__version__)
print("Plotly:    ", plotly.__version__)
print("Pydantic:  ", pydantic.__version__)
print("SpekPy:    ", spekpy.__version__)
print("Streamlit: ", streamlit.__version__)
print("xraylib:   OK")
PY
```

---

# 19. Verify complete machine environment

```bash
echo "===== OS ====="
cat /etc/os-release | grep PRETTY_NAME

echo
echo "===== COMPILER ====="
g++ --version | head -1

echo
echo "===== CMAKE ====="
cmake --version | head -1

echo
echo "===== GEANT4 ====="
geant4-config --version

echo
echo "===== PYTHON ====="
python --version

echo
echo "===== PIP ====="
pip --version

echo
echo "===== NODE ====="
node --version

echo
echo "===== NPM ====="
npm --version

echo
echo "===== XRAYLIB ====="
find /usr/include -name xraylib.h
```

---

# 20. Run the Streamlit frontend

Open a new terminal.

Go to the repository:

```bash
cd ~/TEMPO_XRF_REPO
```

Activate the Python environment:

```bash
source .venv/bin/activate
```

Load Geant4 if needed:

```bash
source ~/geant4/geant4-install/bin/geant4.sh
```

Go to the Streamlit frontend:

```bash
cd ~/TEMPO_XRF_REPO/python_code/roboai_xrf_frontend
```

Run:

```bash
python -m streamlit run main.py
```

---

# 21. Useful commands for every new terminal

```bash
cd ~/TEMPO_XRF_REPO
source .venv/bin/activate
source ~/geant4/geant4-install/bin/geant4.sh
```

The Geant4 source command should already run automatically if it was added to `~/.bashrc`.

---

# 22. Save exact Python environment

On the working machine:

```bash
cd ~/TEMPO_XRF_REPO
source .venv/bin/activate
```

Save exact installed Python packages:

```bash
python -m pip freeze > requirements-lock.txt
```

Check:

```bash
cat requirements-lock.txt
```

Commit it:

```bash
git add requirements-lock.txt
git commit -m "Add Python environment lock file"
git push origin front
```

Then on another machine:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
```

---

# 23. Save Node environment information

```bash
node --version > node-version.txt
npm --version >> node-version.txt
```

Check:

```bash
cat node-version.txt
```

---

# 24. Save complete build environment information

```bash
{
    echo "OS:"
    grep PRETTY_NAME /etc/os-release

    echo
    echo "Python:"
    python --version

    echo
    echo "G++:"
    g++ --version | head -1

    echo
    echo "CMake:"
    cmake --version | head -1

    echo
    echo "Geant4:"
    geant4-config --version

    echo
    echo "Node:"
    node --version

    echo
    echo "npm:"
    npm --version
} > environment-info.txt
```

View:

```bash
cat environment-info.txt
```

Commit:

```bash
git add environment-info.txt node-version.txt
git commit -m "Add development environment information"
git push origin front
```

---

# 25. Full clean install summary

The normal order on a new machine is:

```bash
sudo apt update
sudo apt upgrade -y
```

Install Ubuntu dependencies.

Install xraylib.

Install Node.js.

Install Geant4.

Clone repository.

Create `.venv`.

Install Python dependencies.

Install npm dependencies.

Compile Geant4 backend.

Run Streamlit.

---

# 26. After everything is installed

The commands you normally need are only:

```bash
cd ~/TEMPO_XRF_REPO
source .venv/bin/activate
```

Then:

```bash
cd python_code/roboai_xrf_frontend
python -m streamlit run main.py
```

For the visualization manually:

```bash
cd ~/TEMPO_XRF_REPO/roboaixrf/vis
npm run dev -- --host 0.0.0.0
```

For rebuilding Geant4:

```bash
source ~/geant4/geant4-install/bin/geant4.sh

cd ~/TEMPO_XRF_REPO/geant4_code

cmake \
    -S . \
    -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH=$HOME/geant4/geant4-install

cmake --build build -j$(nproc)
```

---

# Useful Git commands

Check branch:

```bash
git branch
```

Pull newest `front` branch:

```bash
git checkout front
git pull origin front
```

Check changed files:

```bash
git status
```

Commit changes:

```bash
git add .
git commit -m "Update project"
git push origin front
```

---

# Important

Do not copy `.venv`, `node_modules`, Geant4 build directories, simulation ROOT outputs, generated visualization JSON files, or temporary uploaded spectra between machines.

Recreate those environments using this README instead.
