#!/usr/bin/env bash
# TEMPO_XRF_REPO - Ubuntu 24.04 machine setup
#
# Usage on a NEW machine:
#
#   git clone --branch front --single-branch \
#     https://github.com/Minmyatngwe/TEMPO_XRF_REPO.git
#   cd TEMPO_XRF_REPO
#   chmod +x setup_tempo_xrf.sh
#   ./setup_tempo_xrf.sh
#
# To only display the commands:
#
#   cat setup_tempo_xrf.sh
#
# This script installs:
#   - Ubuntu build tools and libraries
#   - xraylib C/C++ development library
#   - Geant4 11.4.2 + Geant4 datasets
#   - Node.js 22
#   - Python virtual environment and XRF Python packages
#   - Frontend requirements
#   - Three.js / Plotly.js / Vite npm dependencies
#
# It is designed for Ubuntu 24.04 and is safe to rerun.

set -Eeuo pipefail

trap 'echo; echo "ERROR: setup failed at line $LINENO"; exit 1' ERR

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GEANT4_VERSION="${GEANT4_VERSION:-11.4.2}"
GEANT4_BASE="${GEANT4_BASE:-$HOME/geant4}"

GEANT4_SOURCE_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}"
GEANT4_BUILD_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}-build"
GEANT4_INSTALL_DIR="$GEANT4_BASE/geant4-install"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"
VENV_DIR="$REPO_DIR/.venv"

FRONTEND_DIR="$REPO_DIR/python_code/roboai_xrf_frontend"
VIS_DIR="$REPO_DIR/roboaixrf/vis"

echo "============================================================"
echo " TEMPO XRF machine setup"
echo "============================================================"
echo "Repository : $REPO_DIR"
echo "Geant4     : $GEANT4_VERSION"
echo "Geant4 dir : $GEANT4_INSTALL_DIR"
echo "Python venv: $VENV_DIR"
echo "============================================================"

# ---------------------------------------------------------------------------
# 0. Check operating system
# ---------------------------------------------------------------------------

if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    echo "Detected OS: ${PRETTY_NAME:-unknown}"

    if [[ "${ID:-}" != "ubuntu" ]]; then
        echo "WARNING: this script was written for Ubuntu 24.04."
    fi
fi

# Ask for sudo once near the beginning.
sudo -v

# ---------------------------------------------------------------------------
# 1. Ubuntu/system packages
# ---------------------------------------------------------------------------

echo
echo ">>> Installing Ubuntu packages..."

sudo apt update

# libxrl-dev is normally in Ubuntu's Universe repository.
sudo apt install -y software-properties-common
sudo add-apt-repository -y universe
sudo apt update

sudo apt install -y \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    ninja-build \
    pkg-config \
    git \
    git-lfs \
    curl \
    wget \
    ca-certificates \
    gnupg \
    python3 \
    python3-dev \
    python3-venv \
    python3-pip \
    libexpat1-dev \
    zlib1g-dev \
    libxerces-c-dev \
    nlohmann-json3-dev \
    libxrl-dev \
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

git lfs install

# ---------------------------------------------------------------------------
# 2. Node.js 22
# ---------------------------------------------------------------------------

echo
echo ">>> Checking Node.js..."

NEED_NODE=1

if command -v node >/dev/null 2>&1; then
    NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"

    if [[ "$NODE_MAJOR" -ge 22 ]]; then
        NEED_NODE=0
        echo "Node.js already installed: $(node --version)"
    fi
fi

if [[ "$NEED_NODE" -eq 1 ]]; then
    echo "Installing Node.js 22..."

    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt install -y nodejs
fi

echo "Node: $(node --version)"
echo "npm : $(npm --version)"

# ---------------------------------------------------------------------------
# 3. Geant4 11.4.2
# ---------------------------------------------------------------------------

echo
echo ">>> Checking Geant4..."

GEANT4_OK=0

if [[ -x "$GEANT4_INSTALL_DIR/bin/geant4-config" ]]; then
    INSTALLED_G4_VERSION="$("$GEANT4_INSTALL_DIR/bin/geant4-config" --version || true)"

    if [[ "$INSTALLED_G4_VERSION" == "$GEANT4_VERSION" ]]; then
        GEANT4_OK=1
        echo "Geant4 $GEANT4_VERSION is already installed."
    fi
fi

if [[ "$GEANT4_OK" -eq 0 ]]; then
    echo "Installing Geant4 $GEANT4_VERSION..."

    mkdir -p "$GEANT4_BASE"
    cd "$GEANT4_BASE"

    GEANT4_ARCHIVE="$GEANT4_BASE/geant4-v${GEANT4_VERSION}.tar.gz"
    GEANT4_URL="https://github.com/Geant4/geant4/archive/refs/tags/v${GEANT4_VERSION}.tar.gz"

    if [[ ! -f "$GEANT4_ARCHIVE" ]]; then
        echo "Downloading:"
        echo "$GEANT4_URL"

        curl -fL \
            "$GEANT4_URL" \
            -o "$GEANT4_ARCHIVE"
    fi

    # Re-extract source if it does not exist.
    if [[ ! -d "$GEANT4_SOURCE_DIR" ]]; then
        tar -xzf "$GEANT4_ARCHIVE" -C "$GEANT4_BASE"

        # GitHub extracts this archive as geant4-X.Y.Z.
        EXTRACTED_DIR="$GEANT4_BASE/geant4-${GEANT4_VERSION}"

        if [[ -d "$EXTRACTED_DIR" && "$EXTRACTED_DIR" != "$GEANT4_SOURCE_DIR" ]]; then
            mv "$EXTRACTED_DIR" "$GEANT4_SOURCE_DIR"
        fi
    fi

    rm -rf "$GEANT4_BUILD_DIR"
    mkdir -p "$GEANT4_BUILD_DIR"
    mkdir -p "$GEANT4_INSTALL_DIR"

    cmake \
        -S "$GEANT4_SOURCE_DIR" \
        -B "$GEANT4_BUILD_DIR" \
        -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="$GEANT4_INSTALL_DIR" \
        -DGEANT4_BUILD_MULTITHREADED=ON \
        -DGEANT4_INSTALL_DATA=ON \
        -DGEANT4_INSTALL_EXAMPLES=OFF \
        -DGEANT4_USE_GDML=ON \
        -DGEANT4_USE_SYSTEM_EXPAT=ON \
        -DGEANT4_USE_SYSTEM_XERCESC=ON \
        -DGEANT4_USE_OPENGL_X11=OFF \
        -DGEANT4_USE_QT=OFF

    cmake --build "$GEANT4_BUILD_DIR" -j"$(nproc)"
    cmake --install "$GEANT4_BUILD_DIR"
fi

# Activate Geant4 for the rest of this setup.
# shellcheck disable=SC1091
source "$GEANT4_INSTALL_DIR/bin/geant4.sh"

echo "Geant4: $(geant4-config --version)"

# Add Geant4 environment setup to ~/.bashrc, but do not duplicate it.
GEANT4_SOURCE_LINE="source \"$GEANT4_INSTALL_DIR/bin/geant4.sh\""

if ! grep -Fqx "$GEANT4_SOURCE_LINE" "$HOME/.bashrc" 2>/dev/null; then
    {
        echo
        echo "# TEMPO_XRF Geant4"
        echo "$GEANT4_SOURCE_LINE"
    } >> "$HOME/.bashrc"
fi

# ---------------------------------------------------------------------------
# 4. Python virtual environment
# ---------------------------------------------------------------------------

echo
echo ">>> Creating Python virtual environment..."

cd "$REPO_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade \
    pip \
    setuptools \
    wheel

# ---------------------------------------------------------------------------
# 5. Python dependencies
# ---------------------------------------------------------------------------

echo
echo ">>> Installing Python dependencies..."

# Current frontend requirements in the front branch include:
#   streamlit>=1.40
#   pandas>=2.2
#   plotly>=5.24
#   numpy>=1.26
#
# Prefer the repo's own requirements file when present.
if [[ -f "$FRONTEND_DIR/requirements.txt" ]]; then
    python -m pip install -r "$FRONTEND_DIR/requirements.txt"
else
    python -m pip install \
        "streamlit>=1.40" \
        "pandas>=2.2" \
        "plotly>=5.24" \
        "numpy>=1.26"
fi

# Packages used by the XRF backend / analysis code.
python -m pip install \
    pydantic \
    spekpy \
    uproot \
    awkward \
    xraylib

# Install the local repository as an editable Python package if it has normal
# packaging metadata. Otherwise install the published roboaixrf package if
# roboaixrf cannot already be imported.
if [[ -f "$REPO_DIR/pyproject.toml" || \
      -f "$REPO_DIR/setup.py" || \
      -f "$REPO_DIR/setup.cfg" ]]; then

    echo
    echo ">>> Installing local repository in editable mode..."
    python -m pip install -e "$REPO_DIR"

elif ! python -c "import roboaixrf" >/dev/null 2>&1; then

    echo
    echo ">>> Installing roboaixrf Python package..."
    python -m pip install roboaixrf
fi

# ---------------------------------------------------------------------------
# 6. JavaScript / Three.js visualization
# ---------------------------------------------------------------------------

echo
echo ">>> Installing visualization npm dependencies..."

if [[ -f "$VIS_DIR/package.json" ]]; then
    cd "$VIS_DIR"

    if [[ -f package-lock.json ]]; then
        npm ci
    else
        npm install
    fi
else
    echo "No package.json found at:"
    echo "  $VIS_DIR"
    echo "Skipping npm installation."
fi

# ---------------------------------------------------------------------------
# 7. Optional Geant4 project build
# ---------------------------------------------------------------------------

echo
echo ">>> Looking for the Geant4 application CMake project..."

PROJECT_CMAKE_DIR=""

if [[ -f "$REPO_DIR/geant4_code/CMakeLists.txt" ]]; then
    PROJECT_CMAKE_DIR="$REPO_DIR/geant4_code"
elif [[ -f "$REPO_DIR/roboaixrf/geant4_code/CMakeLists.txt" ]]; then
    PROJECT_CMAKE_DIR="$REPO_DIR/roboaixrf/geant4_code"
fi

if [[ -n "$PROJECT_CMAKE_DIR" ]]; then
    PROJECT_BUILD_DIR="$PROJECT_CMAKE_DIR/build"

    echo "Found: $PROJECT_CMAKE_DIR"
    echo "Building simulation..."

    rm -rf "$PROJECT_BUILD_DIR"

    cmake \
        -S "$PROJECT_CMAKE_DIR" \
        -B "$PROJECT_BUILD_DIR" \
        -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_PREFIX_PATH="$GEANT4_INSTALL_DIR"

    cmake --build "$PROJECT_BUILD_DIR" -j"$(nproc)"
else
    echo "No known Geant4 CMakeLists.txt location found."
    echo "Skipping application compilation."
fi

# ---------------------------------------------------------------------------
# 8. Verification
# ---------------------------------------------------------------------------

echo
echo "============================================================"
echo " Verifying installation"
echo "============================================================"

echo
echo "Compiler:"
g++ --version | head -n 1

echo
echo "CMake:"
cmake --version | head -n 1

echo
echo "Geant4:"
geant4-config --version

echo
echo "Python:"
python --version

echo
echo "pip:"
python -m pip --version

echo
echo "Node:"
node --version

echo
echo "npm:"
npm --version

echo
echo "xraylib C/C++ header:"
find /usr/include -name xraylib.h -print | head -n 5

echo
echo "Python import check:"

python - <<'PY'
import sys

import numpy
import pandas
import plotly
import pydantic
import streamlit
import spekpy
import uproot
import awkward
import xraylib

print("Python     :", sys.version.split()[0])
print("NumPy      :", numpy.__version__)
print("Pandas     :", pandas.__version__)
print("Plotly     :", plotly.__version__)
print("Pydantic   :", pydantic.__version__)
print("Streamlit  :", streamlit.__version__)
print("SpekPy     :", spekpy.__version__)
print("Uproot     :", uproot.__version__)
print("Awkward    :", awkward.__version__)
print("xraylib    : imported successfully")
PY

echo
echo "============================================================"
echo " SETUP COMPLETE"
echo "============================================================"
echo
echo "For future terminals run:"
echo
echo "  cd \"$REPO_DIR\""
echo "  source \"$VENV_DIR/bin/activate\""
echo
echo "Geant4 will also be loaded automatically by ~/.bashrc."
echo
echo "To run the Streamlit frontend:"
echo
echo "  cd \"$FRONTEND_DIR\""
echo "  source \"$VENV_DIR/bin/activate\""
echo "  python -m streamlit run main.py"
echo
echo "To start the visualization manually, if needed:"
echo
echo "  cd \"$VIS_DIR\""
echo "  npx vite --host 0.0.0.0"
echo
