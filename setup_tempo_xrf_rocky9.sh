#!/usr/bin/env bash
# TEMPO_XRF_REPO setup for Rocky Linux 9 / RHEL 9 family
#
# This script may be launched from ANY directory inside the Git repository.
# It automatically finds the repository root.
#
# Installs:
#   - GCC/G++/CMake/Ninja and build dependencies
#   - Python 3.11 + virtual environment
#   - Node.js 22 + npm
#   - xraylib 4.2.1 C/C++ library
#   - Geant4 11.4.2 + datasets
#   - Python frontend/backend dependencies
#   - visualization npm dependencies
#   - builds the Geant4 backend

set -Eeuo pipefail

trap 'echo; echo "ERROR: setup failed at line $LINENO"; exit 1' ERR

GEANT4_VERSION="${GEANT4_VERSION:-11.4.2}"
XRAYLIB_VERSION="${XRAYLIB_VERSION:-4.2.1}"

GEANT4_BASE="${GEANT4_BASE:-$HOME/geant4}"
GEANT4_SOURCE_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}"
GEANT4_BUILD_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}-build"
GEANT4_INSTALL_DIR="$GEANT4_BASE/geant4-install"

XRAYLIB_BASE="${XRAYLIB_BASE:-$HOME/xraylib}"
XRAYLIB_SOURCE_DIR="$XRAYLIB_BASE/xraylib-${XRAYLIB_VERSION}"
XRAYLIB_BUILD_DIR="$XRAYLIB_BASE/xraylib-${XRAYLIB_VERSION}-build"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find the actual Git repository root even if this script is stored/run from
# python_code/roboai_xrf_frontend or another subdirectory.
REPO_DIR="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -z "$REPO_DIR" ]]; then
    REPO_DIR="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || true)"
fi

if [[ -z "$REPO_DIR" ]]; then
    echo "ERROR: Could not determine TEMPO_XRF_REPO Git root."
    echo "Run this script somewhere inside the cloned TEMPO_XRF_REPO repository."
    exit 1
fi

FRONTEND_DIR="$REPO_DIR/python_code/roboai_xrf_frontend"
VIS_DIR="$REPO_DIR/roboaixrf/vis"
VENV_DIR="$REPO_DIR/.venv"

echo "============================================================"
echo " TEMPO XRF - Rocky Linux 9 setup"
echo "============================================================"
echo "Repository : $REPO_DIR"
echo "Frontend   : $FRONTEND_DIR"
echo "Geant4     : $GEANT4_VERSION"
echo "Geant4 dir : $GEANT4_INSTALL_DIR"
echo "Python venv: $VENV_DIR"
echo "============================================================"

# ---------------------------------------------------------------------------
# 0. OS check
# ---------------------------------------------------------------------------

if [[ ! -f /etc/os-release ]]; then
    echo "ERROR: /etc/os-release not found."
    exit 1
fi

. /etc/os-release
echo "Detected OS: ${PRETTY_NAME:-unknown}"

if ! command -v dnf >/dev/null 2>&1; then
    echo "ERROR: dnf was not found."
    exit 1
fi

sudo -v

# ---------------------------------------------------------------------------
# 1. Repositories and system build dependencies
# ---------------------------------------------------------------------------

echo
echo ">>> Preparing Rocky/RHEL repositories..."

sudo dnf install -y dnf-plugins-core epel-release

# Rocky/RHEL 9 development packages such as some EPEL dependencies may need CRB.
sudo dnf config-manager --set-enabled crb || true

sudo dnf makecache

echo
echo ">>> Installing build dependencies..."

sudo dnf install -y \
    gcc \
    gcc-c++ \
    make \
    cmake \
    ninja-build \
    meson \
    pkgconf-pkg-config \
    git \
    git-lfs \
    curl \
    wget \
    ca-certificates \
    gnupg2 \
    tar \
    gzip \
    unzip \
    python3.11 \
    python3.11-devel \
    python3.11-pip \
    expat-devel \
    zlib-devel \
    xerces-c-devel \
    json-devel

git lfs install

echo
echo "Compiler: $(g++ --version | head -n 1)"
echo "CMake   : $(cmake --version | head -n 1)"
echo "Python  : $(python3.11 --version)"

# ---------------------------------------------------------------------------
# 2. Node.js 22
# ---------------------------------------------------------------------------

echo
echo ">>> Checking Node.js 22..."

NEED_NODE=1

if command -v node >/dev/null 2>&1; then
    NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
    if [[ "$NODE_MAJOR" -ge 22 ]]; then
        NEED_NODE=0
    fi
fi

if [[ "$NEED_NODE" -eq 1 ]]; then
    echo "Installing Node.js 22 from NodeSource RPM repository..."

    curl -fsSL https://rpm.nodesource.com/setup_22.x \
        -o /tmp/nodesource_setup.sh

    sudo bash /tmp/nodesource_setup.sh
    sudo dnf install -y nodejs
    rm -f /tmp/nodesource_setup.sh
fi

echo "Node: $(node --version)"
echo "npm : $(npm --version)"

# ---------------------------------------------------------------------------
# 3. xraylib C/C++ library
# ---------------------------------------------------------------------------

echo
echo ">>> Checking xraylib C/C++ library..."

export PKG_CONFIG_PATH="/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:${LD_LIBRARY_PATH:-}"

if pkg-config --exists libxrl 2>/dev/null; then
    echo "xraylib C/C++ already installed: $(pkg-config --modversion libxrl)"
else
    echo "Building xraylib ${XRAYLIB_VERSION} from source..."

    mkdir -p "$XRAYLIB_BASE"

    XRAYLIB_ARCHIVE="$XRAYLIB_BASE/xraylib-${XRAYLIB_VERSION}.tar.gz"
    XRAYLIB_URL="https://github.com/tschoonj/xraylib/archive/refs/tags/xraylib-${XRAYLIB_VERSION}.tar.gz"

    if [[ ! -f "$XRAYLIB_ARCHIVE" ]]; then
        curl -fL "$XRAYLIB_URL" -o "$XRAYLIB_ARCHIVE"
    fi

    rm -rf "$XRAYLIB_SOURCE_DIR" "$XRAYLIB_BUILD_DIR"
    mkdir -p "$XRAYLIB_SOURCE_DIR"

    tar -xzf "$XRAYLIB_ARCHIVE" \
        -C "$XRAYLIB_SOURCE_DIR" \
        --strip-components=1

    meson setup \
        "$XRAYLIB_BUILD_DIR" \
        "$XRAYLIB_SOURCE_DIR" \
        --prefix=/usr/local \
        --libdir=lib64 \
        --buildtype=release \
        -Dpython-bindings=disabled \
        -Dpython-numpy-bindings=disabled \
        -Dfortran-bindings=disabled

    meson compile -C "$XRAYLIB_BUILD_DIR"
    sudo meson install -C "$XRAYLIB_BUILD_DIR"
    sudo ldconfig
fi

if ! pkg-config --exists libxrl; then
    echo "ERROR: xraylib C/C++ installation was not detected."
    exit 1
fi

echo "xraylib C/C++: $(pkg-config --modversion libxrl)"

# Persist /usr/local library paths.
XRAYLIB_ENV_START="# >>> TEMPO_XRF xraylib >>>"

if ! grep -Fq "$XRAYLIB_ENV_START" "$HOME/.bashrc" 2>/dev/null; then
    {
        echo
        echo "$XRAYLIB_ENV_START"
        echo 'export PKG_CONFIG_PATH="/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH:-}"'
        echo 'export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:${LD_LIBRARY_PATH:-}"'
        echo "# <<< TEMPO_XRF xraylib <<<"
    } >> "$HOME/.bashrc"
fi

# ---------------------------------------------------------------------------
# 4. Geant4 11.4.2
# ---------------------------------------------------------------------------

echo
echo ">>> Checking Geant4 ${GEANT4_VERSION}..."

GEANT4_OK=0

if [[ -x "$GEANT4_INSTALL_DIR/bin/geant4-config" ]]; then
    INSTALLED_G4_VERSION="$("$GEANT4_INSTALL_DIR/bin/geant4-config" --version || true)"

    if [[ "$INSTALLED_G4_VERSION" == "$GEANT4_VERSION" ]]; then
        GEANT4_OK=1
        echo "Geant4 ${GEANT4_VERSION} already installed."
    fi
fi

if [[ "$GEANT4_OK" -eq 0 ]]; then
    echo "Installing Geant4 ${GEANT4_VERSION}..."

    mkdir -p "$GEANT4_BASE"

    GEANT4_ARCHIVE="$GEANT4_BASE/geant4-v${GEANT4_VERSION}.tar.gz"
    GEANT4_URL="https://github.com/Geant4/geant4/archive/refs/tags/v${GEANT4_VERSION}.tar.gz"

    if [[ ! -f "$GEANT4_ARCHIVE" ]]; then
        curl -fL "$GEANT4_URL" -o "$GEANT4_ARCHIVE"
    fi

    if [[ ! -d "$GEANT4_SOURCE_DIR" ]]; then
        tar -xzf "$GEANT4_ARCHIVE" -C "$GEANT4_BASE"

        EXTRACTED_DIR="$GEANT4_BASE/geant4-${GEANT4_VERSION}"

        if [[ -d "$EXTRACTED_DIR" && "$EXTRACTED_DIR" != "$GEANT4_SOURCE_DIR" ]]; then
            mv "$EXTRACTED_DIR" "$GEANT4_SOURCE_DIR"
        fi
    fi

    rm -rf "$GEANT4_BUILD_DIR"
    mkdir -p "$GEANT4_BUILD_DIR" "$GEANT4_INSTALL_DIR"

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

if [[ ! -f "$GEANT4_INSTALL_DIR/bin/geant4.sh" ]]; then
    echo "ERROR: Geant4 environment script was not installed:"
    echo "  $GEANT4_INSTALL_DIR/bin/geant4.sh"
    exit 1
fi

# shellcheck disable=SC1091
source "$GEANT4_INSTALL_DIR/bin/geant4.sh"

echo "Geant4: $(geant4-config --version)"

GEANT4_SOURCE_LINE="source \"$GEANT4_INSTALL_DIR/bin/geant4.sh\""

if ! grep -Fqx "$GEANT4_SOURCE_LINE" "$HOME/.bashrc" 2>/dev/null; then
    {
        echo
        echo "# TEMPO_XRF Geant4"
        echo "$GEANT4_SOURCE_LINE"
    } >> "$HOME/.bashrc"
fi

# ---------------------------------------------------------------------------
# 5. Python 3.11 virtual environment
# ---------------------------------------------------------------------------

echo
echo ">>> Creating Python 3.11 virtual environment..."

cd "$REPO_DIR"

# Recreate an old venv if it was made with Python 3.9.
if [[ -x "$VENV_DIR/bin/python" ]]; then
    VENV_PY="$("$VENV_DIR/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' || true)"

    if [[ "$VENV_PY" != "3.11" ]]; then
        echo "Existing venv uses Python $VENV_PY; recreating with Python 3.11."
        rm -rf "$VENV_DIR"
    fi
fi

if [[ ! -d "$VENV_DIR" ]]; then
    python3.11 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel

echo "Venv Python: $(python --version)"
echo "Venv pip   : $(python -m pip --version)"

# ---------------------------------------------------------------------------
# 6. Python dependencies
# ---------------------------------------------------------------------------

echo
echo ">>> Installing Python dependencies..."

if [[ -f "$FRONTEND_DIR/requirements.txt" ]]; then
    python -m pip install -r "$FRONTEND_DIR/requirements.txt"
else
    python -m pip install \
        "streamlit>=1.40" \
        "pandas>=2.2" \
        "plotly>=5.24" \
        "numpy>=1.26"
fi

python -m pip install \
    pydantic \
    spekpy \
    uproot \
    awkward \
    xraylib

# Install this repository if it is a Python package.
if [[ -f "$REPO_DIR/pyproject.toml" || \
      -f "$REPO_DIR/setup.py" || \
      -f "$REPO_DIR/setup.cfg" ]]; then
    echo
    echo ">>> Installing local TEMPO/XRF package..."
    python -m pip install -e "$REPO_DIR"
fi

# Make repository imports available even if package metadata is elsewhere.
export PYTHONPATH="$REPO_DIR:${PYTHONPATH:-}"

# ---------------------------------------------------------------------------
# 7. JavaScript visualization
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
    echo "WARNING: $VIS_DIR/package.json not found; skipping npm install."
fi

# ---------------------------------------------------------------------------
# 8. Build Geant4 backend
# ---------------------------------------------------------------------------

echo
echo ">>> Looking for Geant4 backend..."

PROJECT_CMAKE_DIR=""

if [[ -f "$REPO_DIR/geant4_code/CMakeLists.txt" ]]; then
    PROJECT_CMAKE_DIR="$REPO_DIR/geant4_code"
elif [[ -f "$REPO_DIR/roboaixrf/geant4_code/CMakeLists.txt" ]]; then
    PROJECT_CMAKE_DIR="$REPO_DIR/roboaixrf/geant4_code"
fi

if [[ -n "$PROJECT_CMAKE_DIR" ]]; then
    PROJECT_BUILD_DIR="$PROJECT_CMAKE_DIR/build"

    echo "Backend source: $PROJECT_CMAKE_DIR"

    rm -rf "$PROJECT_BUILD_DIR"

    cmake \
        -S "$PROJECT_CMAKE_DIR" \
        -B "$PROJECT_BUILD_DIR" \
        -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_PREFIX_PATH="$GEANT4_INSTALL_DIR;/usr/local"

    cmake --build "$PROJECT_BUILD_DIR" -j"$(nproc)"
else
    echo "WARNING: Could not locate the Geant4 backend CMakeLists.txt."
fi

# ---------------------------------------------------------------------------
# 9. Verification
# ---------------------------------------------------------------------------

echo
echo "============================================================"
echo " Verifying installation"
echo "============================================================"

echo "Repository : $REPO_DIR"
echo "G++        : $(g++ --version | head -n 1)"
echo "CMake      : $(cmake --version | head -n 1)"
echo "Geant4     : $(geant4-config --version)"
echo "Python     : $(python --version)"
echo "Node       : $(node --version)"
echo "npm        : $(npm --version)"
echo "xraylib C  : $(pkg-config --modversion libxrl)"

python - <<'PY'
import numpy
import pandas
import plotly
import pydantic
import streamlit
import spekpy
import uproot
import awkward
import xraylib

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
echo "For future terminals:"
echo
echo "  cd \"$REPO_DIR\""
echo "  source \"$GEANT4_INSTALL_DIR/bin/geant4.sh\""
echo "  source \"$VENV_DIR/bin/activate\""
echo "  export PYTHONPATH=\"\$PWD:\${PYTHONPATH:-}\""
echo
echo "Start frontend:"
echo
echo "  cd \"$FRONTEND_DIR\""
echo "  python -m streamlit run main.py"
echo
