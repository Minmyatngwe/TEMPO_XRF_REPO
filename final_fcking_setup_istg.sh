#!/usr/bin/env bash

# TEMPO_XRF_REPO complete setup
# Supports:
#   - Ubuntu / Debian family
#   - Rocky Linux 9 / RHEL 9 family
#
# This script:
#   - installs OS/build dependencies
#   - installs Node.js 22
#   - installs/builds xraylib C/C++
#   - clones/uses TEMPO_XRF_REPO and switches to new_geant4
#   - downloads Geant4 11.4.2
#   - MANDATORILY patches G4EmBiasingManager::ApplyDirectionalSplitting
#   - verifies the null-pointer guard exists before Geant4 is built
#   - builds/installs Geant4
#   - creates the Python virtual environment
#   - installs project Python requirements + h5py + tqdm
#   - installs visualization npm dependencies
#   - builds the XRF Geant4 backend
#
# Optional environment variables:
#   REPO_DIR=/path/to/TEMPO_XRF_REPO
#   REPO_BRANCH=new_geant4
#   GEANT4_BASE=$HOME/geant4
#   GEANT4_VERSION=11.4.2
#   XRAYLIB_VERSION=4.2.1
#   START_STREAMLIT=1

set -Eeuo pipefail

trap 'echo; echo "ERROR: setup failed at line $LINENO"; exit 1' ERR

GEANT4_VERSION="${GEANT4_VERSION:-11.4.2}"
XRAYLIB_VERSION="${XRAYLIB_VERSION:-4.2.1}"
REPO_URL="${REPO_URL:-https://github.com/Minmyatngwe/TEMPO_XRF_REPO.git}"
REPO_BRANCH="${REPO_BRANCH:-new_geant4}"

GEANT4_BASE="${GEANT4_BASE:-$HOME/geant4}"
GEANT4_SOURCE_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}"
GEANT4_BUILD_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}-build"
GEANT4_INSTALL_DIR="$GEANT4_BASE/geant4-install"

XRAYLIB_BASE="${XRAYLIB_BASE:-$HOME/xraylib}"
XRAYLIB_SOURCE_DIR="$XRAYLIB_BASE/xraylib-${XRAYLIB_VERSION}"
XRAYLIB_BUILD_DIR="$XRAYLIB_BASE/xraylib-${XRAYLIB_VERSION}-build"

START_STREAMLIT="${START_STREAMLIT:-0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

banner() {
    echo
    echo "============================================================"
    echo " $1"
    echo "============================================================"
}

# ---------------------------------------------------------------------------
# 0. Detect OS
# ---------------------------------------------------------------------------

if [[ ! -f /etc/os-release ]]; then
    echo "ERROR: /etc/os-release not found."
    exit 1
fi

# shellcheck disable=SC1091
. /etc/os-release

OS_ID="${ID:-unknown}"
OS_LIKE="${ID_LIKE:-}"

if [[ "$OS_ID" == "ubuntu" || "$OS_ID" == "debian" || "$OS_LIKE" == *"debian"* ]]; then
    DISTRO_FAMILY="debian"
elif [[ "$OS_ID" == "rocky" || "$OS_ID" == "rhel" || "$OS_ID" == "almalinux" || "$OS_LIKE" == *"rhel"* || "$OS_LIKE" == *"fedora"* ]]; then
    DISTRO_FAMILY="rhel"
else
    echo "ERROR: Unsupported Linux distribution: ${PRETTY_NAME:-$OS_ID}"
    echo "Supported families: Ubuntu/Debian and Rocky/RHEL."
    exit 1
fi

banner "TEMPO XRF complete setup"
echo "Detected OS     : ${PRETTY_NAME:-unknown}"
echo "Distribution    : $DISTRO_FAMILY"
echo "Geant4 version  : $GEANT4_VERSION"
echo "xraylib version : $XRAYLIB_VERSION"
echo "Target branch   : $REPO_BRANCH"

sudo -v

# ---------------------------------------------------------------------------
# 1. Install system dependencies
# ---------------------------------------------------------------------------

banner "Installing system dependencies"

if [[ "$DISTRO_FAMILY" == "debian" ]]; then
    sudo apt update -y
    sudo apt upgrade -y

    sudo apt install -y \
        git \
        git-lfs \
        curl \
        wget \
        ca-certificates \
        build-essential \
        cmake \
        ninja-build \
        meson \
        python3 \
        python3-dev \
        python3-venv \
        python3-pip \
        pkg-config \
        ffmpeg \
        nlohmann-json3-dev \
        libexpat1-dev \
        zlib1g-dev \
        libxerces-c-dev \
        libx11-dev \
        libxmu-dev \
        libxi-dev \
        libgl1-mesa-dev \
        libglu1-mesa-dev \
        freeglut3-dev \
        mesa-common-dev \
        qtbase5-dev \
        libqt5opengl5-dev \
        libcairo2-dev \
        libpango1.0-dev

    PYTHON_BIN="python3"
else
    sudo dnf install -y dnf-plugins-core epel-release
    sudo dnf config-manager --set-enabled crb || true
    sudo dnf makecache

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
        json-devel \
        libX11-devel \
        libXmu-devel \
        libXi-devel \
        mesa-libGL-devel \
        mesa-libGLU-devel \
        freeglut-devel \
        qt5-qtbase-devel \
        cairo-devel \
        pango-devel

    # ffmpeg may require an additional multimedia repository on some RHEL/Rocky systems.
    sudo dnf install -y ffmpeg || echo "WARNING: ffmpeg was not available from enabled repositories."

    PYTHON_BIN="python3.11"
fi

git lfs install

echo "Compiler: $(g++ --version | head -n 1)"
echo "CMake   : $(cmake --version | head -n 1)"
echo "Python  : $($PYTHON_BIN --version)"

# ---------------------------------------------------------------------------
# 2. Install Node.js 22
# ---------------------------------------------------------------------------

banner "Installing/checking Node.js 22"

NEED_NODE=1

if command -v node >/dev/null 2>&1; then
    NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
    if [[ "$NODE_MAJOR" -ge 22 ]]; then
        NEED_NODE=0
    fi
fi

if [[ "$NEED_NODE" -eq 1 ]]; then
    if [[ "$DISTRO_FAMILY" == "debian" ]]; then
        sudo apt remove -y nodejs npm || true
        sudo apt autoremove -y || true
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
        sudo apt install -y nodejs
    else
        curl -fsSL https://rpm.nodesource.com/setup_22.x -o /tmp/nodesource_setup.sh
        sudo bash /tmp/nodesource_setup.sh
        sudo dnf install -y nodejs
        rm -f /tmp/nodesource_setup.sh
    fi
fi

echo "Node: $(node --version)"
echo "npm : $(npm --version)"
echo "npx : $(npx --version)"



# ---------------------------------------------------------------------------
# 4. Build/install xraylib C/C++ library
# ---------------------------------------------------------------------------

banner "Installing/checking xraylib C/C++"

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
# 5. Download Geant4 11.4.2
# ---------------------------------------------------------------------------

banner "Preparing Geant4 ${GEANT4_VERSION}"

mkdir -p "$GEANT4_BASE"

GEANT4_ARCHIVE="$GEANT4_BASE/geant4-v${GEANT4_VERSION}.tar.gz"
GEANT4_URL="https://gitlab.cern.ch/geant4/geant4/-/archive/v${GEANT4_VERSION}/geant4-v${GEANT4_VERSION}.tar.gz"

if [[ ! -f "$GEANT4_ARCHIVE" ]]; then
    wget -O "$GEANT4_ARCHIVE" "$GEANT4_URL"
fi

if [[ ! -d "$GEANT4_SOURCE_DIR" ]]; then
    tar -xzf "$GEANT4_ARCHIVE" -C "$GEANT4_BASE"
fi

if [[ ! -d "$GEANT4_SOURCE_DIR" ]]; then
    echo "ERROR: Geant4 source directory was not created:"
    echo "  $GEANT4_SOURCE_DIR"
    exit 1
fi

# ---------------------------------------------------------------------------
# 6. MANDATORY Geant4 directional splitting patch
# ---------------------------------------------------------------------------

banner "Applying mandatory Geant4 directional-splitting patch"

PATCH_SCRIPT="$REPO_DIR/python_code/script.py"
BIASING_SOURCE="$GEANT4_SOURCE_DIR/source/processes/electromagnetic/utils/src/G4EmBiasingManager.cc"

if [[ ! -f "$PATCH_SCRIPT" ]]; then
    echo "ERROR: Mandatory patch script not found:"
    echo "  $PATCH_SCRIPT"
    exit 1
fi

if [[ ! -f "$BIASING_SOURCE" ]]; then
    echo "ERROR: Geant4 source file not found:"
    echo "  $BIASING_SOURCE"
    exit 1
fi

# This patch is mandatory. It adds a nullptr guard in
# G4EmBiasingManager::ApplyDirectionalSplitting before dereferencing
# tmpSecondaries[kk].
"$PYTHON_BIN" "$PATCH_SCRIPT" "$GEANT4_SOURCE_DIR"

# Verify that the mandatory nullptr check is actually present.
# Accept either:
#   tmpSecondaries[kk] == nullptr
# or:
#   nullptr == tmpSecondaries[kk]
if ! grep -Eq \
    'tmpSecondaries\[kk\][[:space:]]*==[[:space:]]*nullptr|nullptr[[:space:]]*==[[:space:]]*tmpSecondaries\[kk\]' \
    "$BIASING_SOURCE"; then
    echo
    echo "ERROR: Mandatory directional-splitting patch was NOT detected."
    echo
    echo "The required source file is:"
    echo "  $BIASING_SOURCE"
    echo
    echo "Inside G4EmBiasingManager::ApplyDirectionalSplitting(), the loop must contain:"
    echo
    cat <<'PATCH_EXAMPLE'
for (std::size_t kk = 0; kk < tmpSecondaries.size(); ++kk) {
    if (tmpSecondaries[kk] == nullptr) {
        continue;
    }

    if (tmpSecondaries[kk]->GetParticleDefinition() == theGamma) {
        ...
    }
}
PATCH_EXAMPLE
    echo
    echo "Geant4 will NOT be built without this patch."
    exit 1
fi

echo "Mandatory patch verified in:"
echo "  $BIASING_SOURCE"

# ---------------------------------------------------------------------------
# 7. Build/install Geant4
# ---------------------------------------------------------------------------

banner "Building Geant4 ${GEANT4_VERSION}"

# Reconfigure/rebuild from scratch so a changed Geant4 source file is guaranteed
# to be compiled into the installed libraries.
rm -rf "$GEANT4_BUILD_DIR"
mkdir -p "$GEANT4_BUILD_DIR" "$GEANT4_INSTALL_DIR"

cmake \
    -S "$GEANT4_SOURCE_DIR" \
    -B "$GEANT4_BUILD_DIR" \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$GEANT4_INSTALL_DIR" \
    -DGEANT4_INSTALL_DATA=ON \
    -DGEANT4_BUILD_MULTITHREADED=ON \
    -DGEANT4_INSTALL_EXAMPLES=OFF \
    -DGEANT4_USE_GDML=ON \
    -DGEANT4_USE_SYSTEM_EXPAT=ON \
    -DGEANT4_USE_SYSTEM_XERCESC=ON \
    -DGEANT4_USE_QT=ON \
    -DGEANT4_USE_QT_QT5=ON \
    -DGEANT4_USE_OPENGL_X11=ON \
    -DGEANT4_USE_VTK=OFF

cmake --build "$GEANT4_BUILD_DIR" -j"$(nproc)"
cmake --install "$GEANT4_BUILD_DIR"

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
# 8. Python virtual environment and dependencies
# ---------------------------------------------------------------------------

banner "Creating Python virtual environment"

VENV_DIR="$REPO_DIR/.venv"
cd "$REPO_DIR"

if [[ -x "$VENV_DIR/bin/python" ]]; then
    EXISTING_VENV_PY="$($VENV_DIR/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' || true)"
    TARGET_PY="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

    if [[ "$EXISTING_VENV_PY" != "$TARGET_PY" ]]; then
        echo "Existing venv uses Python $EXISTING_VENV_PY; recreating with Python $TARGET_PY."
        rm -rf "$VENV_DIR"
    fi
fi

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel

banner "Installing Python dependencies"

# Install every project requirements file that exists.
REQUIREMENT_FILES=(
    "$REPO_DIR/requirement.txt"
    "$REPO_DIR/requirements.txt"
    "$REPO_DIR/python_code/roboai_xrf_frontend/requirements.txt"
    "$REPO_DIR/python_code/frontend/requirements.txt"
)

FOUND_REQUIREMENTS=0
for req in "${REQUIREMENT_FILES[@]}"; do
    if [[ -f "$req" ]]; then
        echo "Installing: $req"
        python -m pip install -r "$req"
        FOUND_REQUIREMENTS=1
    fi
done

if [[ "$FOUND_REQUIREMENTS" -eq 0 ]]; then
    echo "WARNING: No requirements file found; installing core frontend packages explicitly."
    python -m pip install \
        "streamlit>=1.40" \
        "pandas>=2.2" \
        "plotly>=5.24" \
        "numpy>=1.26"
fi

# Explicit project/runtime dependencies.
# h5py and tqdm are mandatory additions requested for this setup.
python -m pip install \
    pydantic \
    spekpy \
    uproot \
    awkward \
    xraylib \
    h5py \
    tqdm

# Install repository in editable mode when package metadata exists.
if [[ -f "$REPO_DIR/pyproject.toml" || -f "$REPO_DIR/setup.py" || -f "$REPO_DIR/setup.cfg" ]]; then
    echo ">>> Installing local TEMPO/XRF package in editable mode..."
    python -m pip install -e "$REPO_DIR"
fi

export PYTHONPATH="$REPO_DIR:${PYTHONPATH:-}"

PYTHONPATH_LINE='export PYTHONPATH="'"$REPO_DIR"':${PYTHONPATH:-}"'
if ! grep -Fqx "$PYTHONPATH_LINE" "$HOME/.bashrc" 2>/dev/null; then
    {
        echo
        echo "# TEMPO_XRF Python path"
        echo "$PYTHONPATH_LINE"
    } >> "$HOME/.bashrc"
fi

# ---------------------------------------------------------------------------
# 9. JavaScript visualization dependencies
# ---------------------------------------------------------------------------

banner "Installing visualization npm dependencies"

VIS_DIR=""
for candidate in \
    "$REPO_DIR/roboaixrf/vis" \
    "$REPO_DIR/python_code/vis"; do
    if [[ -f "$candidate/package.json" ]]; then
        VIS_DIR="$candidate"
        break
    fi
done

if [[ -n "$VIS_DIR" ]]; then
    cd "$VIS_DIR"

    if [[ -f package-lock.json ]]; then
        npm ci
    else
        npm install
    fi

    # Keep these explicit because they are required by the visualization code.
    npm install three
    npm install --save-dev vite@5

    npm ls three || true
    npm ls vite || true
else
    echo "WARNING: Visualization package.json was not found; skipping npm install."
fi

# ---------------------------------------------------------------------------
# 10. Build XRF Geant4 backend
# ---------------------------------------------------------------------------

banner "Building XRF Geant4 backend"

PROJECT_CMAKE_DIR=""
for candidate in \
    "$REPO_DIR" \
    "$REPO_DIR/geant4_code" \
    "$REPO_DIR/roboaixrf/geant4_code"; do
    if [[ -f "$candidate/CMakeLists.txt" ]]; then
        PROJECT_CMAKE_DIR="$candidate"
        break
    fi
done

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

    if [[ -f "$PROJECT_BUILD_DIR/sim" ]]; then
        ls -lh "$PROJECT_BUILD_DIR/sim"
    fi
else
    echo "WARNING: Could not locate the XRF backend CMakeLists.txt."
fi

# ---------------------------------------------------------------------------
# 11. Verification
# ---------------------------------------------------------------------------

banner "Verifying installation"

echo "Repository : $REPO_DIR"
echo "Branch     : $(git -C "$REPO_DIR" branch --show-current)"
echo "G++        : $(g++ --version | head -n 1)"
echo "CMake      : $(cmake --version | head -n 1)"
echo "Geant4     : $(geant4-config --version)"
echo "Python     : $(python --version)"
echo "Node       : $(node --version)"
echo "npm        : $(npm --version)"
echo "xraylib C  : $(pkg-config --modversion libxrl)"

python - <<'PY'
import importlib

modules = [
    "numpy",
    "pandas",
    "plotly",
    "pydantic",
    "streamlit",
    "spekpy",
    "uproot",
    "awkward",
    "xraylib",
    "h5py",
    "tqdm",
]

for name in modules:
    mod = importlib.import_module(name)
    version = getattr(mod, "__version__", "imported successfully")
    print(f"{name:<12}: {version}")
PY

# Verify the mandatory patch one final time after installation.
if grep -Eq \
    'tmpSecondaries\[kk\][[:space:]]*==[[:space:]]*nullptr|nullptr[[:space:]]*==[[:space:]]*tmpSecondaries\[kk\]' \
    "$BIASING_SOURCE"; then
    echo "Geant4 patch: VERIFIED"
else
    echo "ERROR: Geant4 patch verification failed unexpectedly."
    exit 1
fi

# ---------------------------------------------------------------------------
# 12. Find frontend and optionally start Streamlit
# ---------------------------------------------------------------------------

FRONTEND_DIR=""
for candidate in \
    "$REPO_DIR/python_code/roboai_xrf_frontend" \
    "$REPO_DIR/python_code/frontend"; do
    if [[ -f "$candidate/main.py" ]]; then
        FRONTEND_DIR="$candidate"
        break
    fi
done

banner "SETUP COMPLETE"

echo "For future terminals:"
echo
printf '  source "%s/bin/geant4.sh"\n' "$GEANT4_INSTALL_DIR"
printf '  source "%s/bin/activate"\n' "$VENV_DIR"
printf '  export PYTHONPATH="%s:${PYTHONPATH:-}"\n' "$REPO_DIR"
echo

if [[ -n "$FRONTEND_DIR" ]]; then
    echo "Start frontend with:"
    echo
    printf '  cd "%s"\n' "$FRONTEND_DIR"
    echo "  python -m streamlit run main.py"
    echo

    if [[ "$START_STREAMLIT" == "1" ]]; then
        cd "$FRONTEND_DIR"
        exec python -m streamlit run main.py
    fi
else
    echo "WARNING: Could not locate frontend main.py."
fi
